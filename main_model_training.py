import os

if __name__ == '__main__':
    if not os.path.exists("dataset"):
        import dataset_preparation_2
    from map_generator import yolo_training
    yolo_training.main()