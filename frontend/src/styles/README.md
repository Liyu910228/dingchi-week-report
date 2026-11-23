# 全局样式目录

- `index.css`：唯一全局入口，只在 `src/main.ts` 导入。
- `tokens.css`：颜色、间距、阴影等主题变量和设计令牌。
- `reset.css`：浏览器默认样式重置和基础元素规则。
- `global.css`：多个页面真正共用的布局或基础类。

页面和组件私有样式不得放在此目录，应与对应 `.vue` 文件同目录、同名，并通过
`<style scoped src="./ComponentName.css"></style>` 引入。
