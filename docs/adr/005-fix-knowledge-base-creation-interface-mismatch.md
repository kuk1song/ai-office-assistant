# ADR-005: 修复知识库创建接口不匹配问题

## 状态
已接受

## 上下文
在重构Agent工具结构后，发现知识库创建功能无法正常工作。用户点击"Create Knowledge Base"按钮后，终端显示"🔧 Creating knowledge base..."但随后没有任何反应，应用程序挂起。

## 问题分析
经过调查发现，问题出现在UI层和Engine层之间的接口不匹配：

### 根本原因
- **Engine层期望**：`create_and_save(uploaded_files: List)` - Streamlit UploadedFile对象列表
- **UI层传递**：`create_and_save(temp_file_paths: List[str])` - 文件路径字符串列表

### 问题来源
在之前的工具重构过程中，我们修改了`AgentEngine`的方法接口以直接处理Streamlit文件对象，但忘记同步更新UI层的调用代码。UI层仍然使用旧的流程：
1. 将上传的文件保存到临时目录
2. 传递文件路径给Engine

## 决策
直接修改UI层代码，使其与新的Engine接口兼容：

### 解决方案
1. **删除中间步骤**：不再将上传文件保存到临时目录
2. **直接传递文件对象**：UI直接将`uploaded_files`传递给Engine
3. **简化错误处理**：利用Engine返回的`failed_files`列表进行错误处理
4. **清理冗余代码**：删除不再需要的`handle_file_upload()`函数

### 修改内容
- **`src/ui/components/upload.py`**：
  - 修改`create_knowledge_base_handler()`直接传递`uploaded_files`
  - 修改`create_add_documents_handler()`使用相同模式
  - 删除`handle_file_upload()`函数
  - 移除临时文件处理逻辑
- **`src/ui/components/__init__.py`**：
  - 移除`handle_file_upload`的导入和导出

## 后果

### 正面影响
- ✅ 知识库创建功能恢复正常
- ✅ 代码更简洁，减少了不必要的文件IO操作
- ✅ 错误处理更精确，能够区分成功和失败的文件
- ✅ 消除了临时文件管理的复杂性

### 经验教训
- 🔄 **接口一致性**：在重构时必须确保所有调用方都同步更新
- 🔄 **端到端测试**：重构后应该进行完整的功能测试
- 🔄 **文档更新**：接口变更应该及时更新相关文档

### 预防措施
- 建立更严格的测试流程
- 在重构时创建接口兼容性检查清单
- 考虑使用类型提示和静态分析工具

## 实现细节

### 修改前（问题代码）
```python
# UI层
temp_file_paths, successful_files = handle_file_upload(unique_files.values(), temp_dir)
chat_engine.create_and_save(temp_file_paths)
```

### 修改后（修复代码）
```python
# UI层  
failed_files = chat_engine.create_and_save(list(unique_files.values()))
```

这次修复强调了在系统重构过程中保持接口一致性的重要性。
