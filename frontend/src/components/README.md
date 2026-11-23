# 全局通用组件

此目录只存放跨功能模块复用、且不属于某个业务领域的 UI 组件，例如基础按钮、弹窗、
分页、提示框。所有组件必须按功能分类到子目录，禁止把 `.vue` 和对应 CSS 平铺在
`components/` 根目录。

推荐分类：

- `actions/`：按钮等操作组件。
- `feedback/`：提示、加载、空状态等反馈组件。
- `form/`：输入框、选择器等表单组件。
- `navigation/`：分页、标签页、面包屑等导航组件。
- `overlay/`：弹窗、抽屉、浮层等覆盖组件。
- `data-display/`：表格、标签、卡片等数据展示组件。

没有对应代码时不创建空分类目录。新增类型不属于现有分类时，可以创建语义清晰的
kebab-case 子目录。

组件必须使用 PascalCase 命名。存在私有样式时，使用同名 CSS 文件并通过 scoped style
的 src 属性引入。例如：`components/feedback/NoticeCenter.vue` 与同目录的
`NoticeCenter.css` 一一对应。

领域组件放到 features/<domain>/components，仅单个页面模块使用的组件放到
views/<module>/components。
