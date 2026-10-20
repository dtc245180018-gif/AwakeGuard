"""Train and evaluate an open/closed-eye SVM using the real MRL Eye dataset.

The test set is held out by *person*, avoiding consecutive video frames from
the same person appearing on both sides of the evaluation.
"""

from __future__ import annotations

import argparse
import io
import json
import random
import zipfile
from collections import defaultdict
from pathlib import Path

import joblib
import numpy as np
from PIL import Image
from sklearn.metrics import (accuracy_score, classification_report,
                             confusion_matrix, f1_score)
from sklearn.model_selection import GroupShuffleSplit
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC

from eye_features import hog_feature

ROOT = Path(__file__).resolve().parent
MODEL_PATH = ROOT / "models" / "eye_state_svm.joblib"
METRICS_PATH = ROOT / "models" / "evaluation.json"


def parse_item(filename: str):
    name = Path(filename).name
    if not name.endswith(".png"):
        return None
    parts = name[:-4].split("_")
    # subject, image ID, gender, glasses, eye state, reflections, light, sensor
    if len(parts) != 8 or parts[4] not in {"0", "1"}:
        return None
    return parts[0], int(parts[4])


def load_mrl(zip_path: Path, maximum: int, seed: int):
    samples = defaultdict(list)
    with zipfile.ZipFile(zip_path) as archive:
        for name in archive.namelist():
            item = parse_item(name)
            if item:
                samples[item].append(name)
        if len({subject for subject, _ in samples}) < 8:
            raise RuntimeError("Bộ dữ liệu cần ảnh mắt của nhiều người khác nhau.")

        randomizer = random.Random(seed)
        chosen = []
        for (subject, label), names in sorted(samples.items()):
            # Balanced sampling within each person's two eye states.
            selected = randomizer.sample(names, min(len(names), maximum))
            chosen.extend((name, subject, label) for name in selected)

        X, y, people = [], [], []
        total = len(chosen)
        for i, (name, subject, label) in enumerate(chosen, 1):
            with Image.open(io.BytesIO(archive.read(name))) as image:
                X.append(hog_feature(image))
            y.append(label)
            people.append(subject)
            if i % 1000 == 0:
                print(f"Đã chuẩn bị {i}/{total} ảnh mắt", flush=True)
    return np.asarray(X, dtype=np.float32), np.asarray(y), np.asarray(people)


def add_custom_training(X, y, train_indices, custom_dir: Path):
    data = [X[train_indices]]
    labels = [y[train_indices]]
    count = 0
    for folder, label in (("closed", 0), ("open", 1)):
        path = custom_dir / folder
        if not path.exists():
            continue
        feats = []
        for name in sorted(path.iterdir()):
            if not name.is_file() or name.suffix.lower() not in {".png", ".jpg", ".jpeg"}:
                continue
            try:
                with Image.open(name) as img:
                    feats.append(hog_feature(img))
            except OSError:
                print(f"Bỏ qua ảnh không đọc được: {name}")
        if feats:
            data.append(np.asarray(feats, dtype=np.float32))
            labels.append(np.full(len(feats), label))
            count += len(feats)
    return np.concatenate(data), np.concatenate(labels), count


def main():
    parser = argparse.ArgumentParser(description="Huấn luyện SVM nhận diện mắt nhắm/mở, kiểm thử tách biệt theo người")
    parser.add_argument("--dataset", required=True, type=Path, help="Đường dẫn đến mrlEyes_2018_01.zip")
    parser.add_argument("--max-per-subject", type=int, default=130,
                        help="Số ảnh tối đa cho mỗi trạng thái và người (mặc định: 130)")
    parser.add_argument("--custom-dir", type=Path, default=ROOT / "data" / "custom",
                        help="Thư mục ảnh mắt tự thu thêm (chỉ dùng huấn luyện)")
    parser.add_argument("--seed", type=int, default=2026)
    args = parser.parse_args()
    if args.max_per_subject < 15:
        parser.error("--max-per-subject phải ít nhất là 15")

    X, y, people = load_mrl(args.dataset, args.max_per_subject, args.seed)
    groups = GroupShuffleSplit(n_splits=1, test_size=0.20, random_state=args.seed)
    training, testing = next(groups.split(X, y, groups=people))
    # Additional held-out people for model selection; never use final test here.
    inner_groups = GroupShuffleSplit(n_splits=1, test_size=0.20, random_state=args.seed + 1)
    tr_rel, val_rel = next(inner_groups.split(X[training], y[training], groups=people[training]))
    tr, val = training[tr_rel], training[val_rel]
    if len(np.unique(y[tr])) != 2 or len(np.unique(y[val])) != 2 or len(np.unique(y[testing])) != 2:
        raise RuntimeError("Một tập dữ liệu chỉ chứa một trạng thái mắt; hãy đổi seed/max-per-subject")
    Xtr, ytr, custom_count = add_custom_training(X, y, tr, args.custom_dir)
    print(f"MRL: huấn luyện {len(tr)} | xác thực {len(val)} | kiểm thử {len(testing)} | tự thu {custom_count}")

    candidates = [("svm_rbf_C1", 1.0), ("svm_rbf_C4", 4.0)]
    rankings = []
    for name, C in candidates:
        classifier = make_pipeline(StandardScaler(), SVC(kernel="rbf", C=C,
                                gamma="scale", probability=True, class_weight="balanced",
                                random_state=args.seed))
        print(f"Đang huấn luyện {name}...", flush=True)
        classifier.fit(Xtr, ytr)
        pred = classifier.predict(X[val])
        score = f1_score(y[val], pred, pos_label=0)
        rankings.append((score, name, C))
        print(f"  F1 mắt nhắm trên tập xác thực = {score:.4f}")
    best_score, best_name, best_C = max(rankings)
    # Refit best model on training + validation people, plus custom photos.
    Xfinal, yfinal, custom_count = add_custom_training(X, y, training, args.custom_dir)
    model = make_pipeline(StandardScaler(), SVC(kernel="rbf", C=best_C,
                          gamma="scale", probability=True, class_weight="balanced",
                          random_state=args.seed))
    model.fit(Xfinal, yfinal)
    pred = model.predict(X[testing])
    metrics = {
        "dataset": "MRL Eye Dataset 2018 (original site: https://mrl.cs.vsb.cz/eyedataset.html)",
        "method": "HOG + standard scaling + RBF SVM; held-out people",
        "labels": {"0": "closed", "1": "open"},
        "seed": args.seed,
        "best_model": best_name,
        "validation_f1_closed": float(best_score),
        "train_images": int(len(training)),
        "test_images": int(len(testing)),
        "custom_training_images": custom_count,
        "train_subjects": sorted(set(people[training].tolist())),
        "test_subjects": sorted(set(people[testing].tolist())),
        "test_accuracy": float(accuracy_score(y[testing], pred)),
        "test_f1_closed": float(f1_score(y[testing], pred, pos_label=0)),
        "confusion_matrix_closed_open": confusion_matrix(y[testing], pred, labels=[0, 1]).tolist(),
        "classification_report": classification_report(
            y[testing], pred, labels=[0, 1], target_names=["closed", "open"],
            output_dict=True, zero_division=0),
        "warning": "MRL uses infrared images. These scores do not measure accuracy on a normal RGB webcam, nor real drowsiness."
    }
    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, MODEL_PATH, compress=3)
    METRICS_PATH.write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Đã lưu mô hình: {MODEL_PATH}")
    print(f"Độ chính xác kiểm thử trên người chưa thấy: {metrics['test_accuracy']:.3%}")
    print(f"F1 mắt nhắm trên người chưa thấy: {metrics['test_f1_closed']:.3f}")
    print("Ma trận nhầm lẫn (hàng=thực tế, cột=dự đoán; nhắm/mở):")
    print(metrics["confusion_matrix_closed_open"])


if __name__ == "__main__":
    main()
