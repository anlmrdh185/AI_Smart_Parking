from ultralytics.data.converter import convert_coco

# 1. Convert the Training set
# labels_dir: where your _annotations.coco.json is
# use_segments: Set to False for simple box detection (parking slots)
convert_coco(labels_dir='dataset/train/', use_segments=False)

# 2. Convert the Validation set
convert_coco(labels_dir='dataset/val/', use_segments=False)

print("Conversion complete! Check your dataset folders for a new 'labels' directory.")