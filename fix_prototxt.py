import os

proto_path = r"C:\Users\танюшка\Desktop\movewell-backend\openpose\models\pose\coco\pose_deploy_linevec.prototxt"

# Правильное содержимое prototxt файла (первые 50 строк для теста)
correct_proto_content = '''name: "Body_pose"
layer {
  name: "image"
  type: "Input"
  top: "image"
  input_param { shape: { dim: 1 dim: 3 dim: 368 dim: 368 } }
}
layer {
  name: "conv1_1"
  type: "Convolution"
  bottom: "image"
  top: "conv1_1"
  convolution_param {
    num_output: 64
    pad: 1
    kernel_size: 3
    stride: 1
  }
}
layer {
  name: "relu1_1"
  type: "ReLU"
  bottom: "conv1_1"
  top: "conv1_1"
}
layer {
  name: "conv1_2"
  type: "Convolution"
  bottom: "conv1_1"
  top: "conv1_2"
  convolution_param {
    num_output: 64
    pad: 1
    kernel_size: 3
    stride: 1
  }
}
layer {
  name: "relu1_2"
  type: "ReLU"
  bottom: "conv1_2"
  top: "conv1_2"
}
layer {
  name: "pool1_stage1"
  type: "Pooling"
  bottom: "conv1_2"
  top: "pool1_stage1"
  pooling_param {
    pool: MAX
    kernel_size: 2
    stride: 2
  }
}'''

# Сохраняем файл заново
with open(proto_path, 'w', encoding='ascii') as f:
    f.write(correct_proto_content)

print(f"Файл перезаписан: {proto_path}")
print(f"Размер: {os.path.getsize(proto_path)} байт")