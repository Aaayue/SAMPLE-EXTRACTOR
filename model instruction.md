# 程序说明文档


## 主要功能

针对单一数据源，提供了基于地理位置信息（lat, lon）的时间序列提取，插值，SG滤波，训练/测试数据分割，以及模型训练功能。文档将会包括以上各功能说明。


---

## 样本时间序列提取

文件路径： /preprocess/extract_points/extractor.py

功能说明： 基于输入文件中的地理坐标信息，提取对应点坐标在给定时间范围内，指定波段的反射率时间序列信息。具体可参考代码内说明。

参数说明：

    input_file/out_path： 输入输出文件目录
    sentinel_listfile/landsat_listfile/modis_file_list： sentinel/landsat/modis大气校正后数据存放路径记录所在json文件路径
    intermediate_out_path： 中间文件存放路径
    dynamic_task： 提取任务字典，包含起始时间和作物地理信息文件，并分别一一对应
    extracting_state： 提取任务选项，landsat(1)和S1(2)

---

## 数据预处理（插值滤波，数据分割）
文件路径： /preprocess/preprocessed_points/preprocess_main.py

功能说明： 实现对原始时间序列的插值和平滑，添加样本标签，并依据时间对数据集进行训练/测试分割。涉及两大主要功能，插值滤波和数据分割。

参数说明：

参数修改在辅助文件中进行，manifest_list.py和settings.py

    CROP_TYPES： 作物名称，包含所有模型分类涉及的正负样本作物种类
    SG： 平滑滤波参数，[窗口大小， 几何级数]
    PROCESS_STATE： 预处理状态，0（插值滤波+数据分割），1（插值滤波），2（数据分割）
    QUANTITY： 数据集大小，每个文件的样本点数目
    REF_TYPES_L/REF_TYPES_S： 数据源波段名称
    EXTRACTED_PATH： 时间序列提取文件路径
    PREPROCESSED_PATH： 插值滤波结果输出路径
    PRETRAIN_PATH： 数据分割结果输出路径
    INDICATOR： 作物标签


### 插值滤波

文件路径： /preprocess/preprocessed_points/preprocessor.py

功能说明： 对原始时间序列进行基于指定时间频率的插值和SG平滑。具体可参考代码内说明。

### 数据分割

文件路径： /preprocess/preprocessed_points/pretrainer.py

功能说明： 添加标签并完成数据集训练/测试分割。

---

## 模型训练

文件路径： /model/RNN/

功能说明： 以LSTM为原型实现的分类模型，总体结构相同。

参数说明：（不包含LSTM自带参数）

    model_dir： 模型存放路径
    num_input： 输入波段数目
    timesteps： 输入时间序列长度
    num_classes： 类别数目，可根据需要进行标签重定义
    display_step： 结果打印的间隔迭代次数
    train： 训练数据文件路径，数据预处理的结果文件
    test： 测试文件路径，数据预处理的结果文件
    n： 测试数据分包数目，保持test_size与n不存在整数倍关系

---

以上

-- U, 2019/5/8






