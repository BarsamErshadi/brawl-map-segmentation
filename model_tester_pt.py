from ultralytics import YOLO
import cv2
import matplotlib.pyplot as plt
from ultralytics.engine.results import Results

model = YOLO(r'C:\Dev\Python\PylaWallDetector\runs\train\yolo_run_v1\weights\best.pt')
model = YOLO(r'C:\Dev\Python\PylaWallDetector\best.pt')

image_path = 'test_images/img_23.png'

image = cv2.imread(image_path)
results = model(image, conf=0.1, device="cuda")
result: Results = results[0]
ids_to_not_show= [0]
# filtered_boxes = [box for box in result.boxes if box.cls not in ids_to_not_show]
# result.boxes = filtered_boxes
annotated_frame = result.plot(
    labels=False,  # Show class labels
    #boxes=False,   # Show bounding boxes (optional, set to False to hide)
    #masks=True    # CRUCIAL: Ensure masks are plotted
)
plt.imshow(cv2.cvtColor(annotated_frame, cv2.COLOR_BGR2RGB))
plt.axis('off')
plt.show()
