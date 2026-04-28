import cv2
import numpy as np
import torch
from PIL import Image
import onnxruntime as ort
from matplotlib import pyplot as plt
from ultralytics.engine.results import Results
from ultralytics.utils import ops

import cv2
import numpy as np
import onnxruntime as ort
import matplotlib.pyplot as plt
from PIL import Image


class Detect:
    def __init__(self, model_path, ignore_classes=None, classes=None, input_size=(640, 640)):
        self.model_path = model_path
        self.classes = classes
        self.ignore_classes = ignore_classes if ignore_classes else []
        self.input_size = input_size
        self.model, self.device = self.load_model()

    def load_model(self):
        available_providers = ort.get_available_providers()
        if "CUDAExecutionProvider" in available_providers:
            onnx_provider = "CUDAExecutionProvider"
            print("Using CUDA GPU")
        elif "DmlExecutionProvider" in available_providers:
            onnx_provider = "DmlExecutionProvider"
            print("Using GPU")
        elif "AzureExecutionProvider" in available_providers:
            onnx_provider = "AzureExecutionProvider"
        else:
            print("Using CPU as no GPU provider found")
            onnx_provider = "CPUExecutionProvider"

        so = ort.SessionOptions()
        so.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
        model = ort.InferenceSession(self.model_path, sess_options=so, providers=[onnx_provider])

        return model, onnx_provider

    def preprocess_image(self, img):
        if isinstance(img, Image.Image):
            img = np.array(img)

        h, w, _ = img.shape
        scale = min(self.input_size[0] / h, self.input_size[1] / w)
        new_w = int(w * scale)
        new_h = int(h * scale)

        resized_img = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_LINEAR)

        padded_img = np.full((self.input_size[1], self.input_size[0], 3), 128, dtype=np.uint8)
        padded_img[:new_h, :new_w, :] = resized_img

        padded_img = cv2.cvtColor(padded_img, cv2.COLOR_BGR2RGB)
        padded_img = padded_img.astype(np.float32) / 255.0
        padded_img = np.transpose(padded_img, (2, 0, 1))
        padded_img = np.expand_dims(padded_img, axis=0)

        return torch.from_numpy(padded_img), new_w, new_h

    def postprocess(self, preds, img, orig_img_shape, resized_shape):
        preds = ops.non_max_suppression(
            preds,
            conf_thres=0.25,
            iou_thres=0.6,
            classes=None,
            agnostic=False,
        )

        orig_h, orig_w = orig_img_shape
        resized_w, resized_h = resized_shape

        scale_w = orig_w / resized_w
        scale_h = orig_h / resized_h

        results = []
        for pred in preds:
            if len(pred):
                pred[:, 0] *= scale_w  # x1
                pred[:, 1] *= scale_h  # y1
                pred[:, 2] *= scale_w  # x2
                pred[:, 3] *= scale_h  # y2
                results.append(pred.cpu().numpy())

        return results

    def detect_objects(self, img):
        if isinstance(img, Image.Image):
            img = np.array(img)
            img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
        orig_h, orig_w = img.shape[:2]
        orig_img_shape = (orig_h, orig_w)

        preprocessed_img, resized_w, resized_h = self.preprocess_image(img)
        resized_shape = (resized_w, resized_h)

        outputs = self.model.run(None, {'images': preprocessed_img.cpu().numpy()})
        detections = self.postprocess(torch.from_numpy(outputs[0]), preprocessed_img, orig_img_shape, resized_shape)

        results = []
        for detection in detections:
            for *xyxy, conf, cls in detection:
                x1, y1, x2, y2 = map(int, xyxy)
                class_id = int(cls)
                class_name = self.classes[class_id]

                if class_id in self.ignore_classes or class_name in self.ignore_classes:
                    continue
                results.append([class_name, x1, y1, x2, y2, conf])

        return results


# Use the detect object
model_path = r'C:\Dev\Python\PylaWallDetector\map_generator\runs\train\yolov11_gamebot_run7\weights\best.onnx'
Detect_tile_detector = Detect(
    model_path,
    classes=["bush", "blue_post", "block_of_stone&grass", "cubic_wall", "red_pottery",
             "wooden_barrel", "cactus", "wooden_box", "wooden_fence", "invincible_wall",
             "yellow_wall", "blue_barrel", "metallic_fence", "blue_weights", "potted_plant", "star_block", "bumper", "yellow_metallic_box"]
)

image_path = 'test_images/dnplayer_6k2rPWZHOC.png'

image = cv2.imread(image_path)

# Detect objects
results = Detect_tile_detector.detect_objects(image)

# Annotate the image
for result in results:
    class_name, x1, y1, x2, y2, conf = result
    cv2.rectangle(image, (x1, y1), (x2, y2), (0, 255, 0), 2)
    cv2.putText(image, f'{class_name} {conf:.2f}', (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)

# Display the result
plt.imshow(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
plt.axis('off')
plt.show()
