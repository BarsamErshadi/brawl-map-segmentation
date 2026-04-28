import os
import yaml
from ultralytics import YOLO


def train_yolov11(
        data_yaml='data.yaml',
        model_name='yolo11n-seg.pt',
        epochs=100,
        batch=32,
        imgsz=640,
        device='0',
        project='runs/train',
        name='yolov11_gamebot',
        exist_ok=True,
        verbose=True,
        resume=False,
):
    print(f"Loading YOLOv11 model: {model_name}...")

    if resume:
        checkpoint = os.path.join(project, name, 'weights', 'last.pt')
        if isinstance(resume, str):
            checkpoint = resume
        print(f"Resuming training from checkpoint: {checkpoint}")
        model = YOLO(checkpoint)
    else:
        model = YOLO(model_name)

    print("Starting training with optimized Game Bot settings...")

    results = model.train(
        data=data_yaml,
        epochs=epochs,
        batch=batch,
        imgsz=imgsz,
        device=device,
        project=project,
        name=name,
        exist_ok=exist_ok,
        resume=resume,
        verbose=verbose,

        # Hardware Optimization
        patience=20,

        # --- Game-Specific Augmentations ---
        degrees=0.0,
        translate=0.1,
        scale=0.5,
        shear=0.0,
        perspective=0.0,
        flipud=0.0,
        fliplr=0.5,
        mosaic=1.0,
        mixup=0.0,
        hsv_h=0.015,
        hsv_s=0.7,
        hsv_v=0.4,
    )

    print("Training completed.")
    return model


def export_yolov11(model, device='0'):
    print("Exporting model to ONNX format...")
    model.export(format='onnx', dynamic=False, simplify=True, device=device)
    print("Export completed.")


def main():
    # --- PATHS ---
    data_yaml = 'map_generator/data.yaml'

    # --- SETTINGS ---
    model_name = 'yolo11n-seg.pt'
    epochs = 100
    imgsz = 640
    batch = 4
    device = '0'
    project = 'runs/train'
    run_name = 'yolo_run_v1'

    if not os.path.isfile(data_yaml):
        raise FileNotFoundError(f"Data configuration file '{data_yaml}' not found.")

    # 1. TRAIN
    model = train_yolov11(
        data_yaml=data_yaml,
        model_name=model_name,
        epochs=epochs,
        batch=batch,
        imgsz=imgsz,
        device=device,
        project=project,
        name=run_name,
        resume=True
    )

    # 2. EXPORT
    export_yolov11(model, device=device)

