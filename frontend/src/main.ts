import ElementPlus from 'element-plus'
import zhCn from 'element-plus/es/locale/lang/zh-cn'
import 'element-plus/dist/index.css'
import 'highlight.js/styles/github.css'
import 'katex/dist/katex.min.css'
import { createApp } from 'vue'

import App from './App.vue'
import './styles/main.css'
import './styles/markdown.css'

createApp(App).use(ElementPlus, { locale: zhCn }).mount('#app')
