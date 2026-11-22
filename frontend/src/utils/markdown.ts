import hljs from 'highlight.js/lib/core'
import bash from 'highlight.js/lib/languages/bash'
import cpp from 'highlight.js/lib/languages/cpp'
import css from 'highlight.js/lib/languages/css'
import go from 'highlight.js/lib/languages/go'
import java from 'highlight.js/lib/languages/java'
import javascript from 'highlight.js/lib/languages/javascript'
import json from 'highlight.js/lib/languages/json'
import markdown from 'highlight.js/lib/languages/markdown'
import python from 'highlight.js/lib/languages/python'
import sql from 'highlight.js/lib/languages/sql'
import typescript from 'highlight.js/lib/languages/typescript'
import xml from 'highlight.js/lib/languages/xml'
import yaml from 'highlight.js/lib/languages/yaml'
import MarkdownIt from 'markdown-it'
import markdownItKatex from '@vscode/markdown-it-katex'

hljs.registerLanguage('bash', bash)
hljs.registerLanguage('shell', bash)
hljs.registerLanguage('cpp', cpp)
hljs.registerLanguage('css', css)
hljs.registerLanguage('go', go)
hljs.registerLanguage('java', java)
hljs.registerLanguage('javascript', javascript)
hljs.registerLanguage('js', javascript)
hljs.registerLanguage('json', json)
hljs.registerLanguage('markdown', markdown)
hljs.registerLanguage('python', python)
hljs.registerLanguage('py', python)
hljs.registerLanguage('sql', sql)
hljs.registerLanguage('typescript', typescript)
hljs.registerLanguage('ts', typescript)
hljs.registerLanguage('html', xml)
hljs.registerLanguage('xml', xml)
hljs.registerLanguage('yaml', yaml)
hljs.registerLanguage('yml', yaml)

const md = new MarkdownIt({
  html: false, // 不解析原始 HTML，避免注入
  linkify: true,
  breaks: true, // 聊天场景下单个换行也生效
  typographer: true,
})

// 行内 $...$ 与块级 $$...$$ 数学公式；公式不合法时输出红字而不是抛错
md.use(markdownItKatex, { throwOnError: false, errorColor: '#d64545' })

const escapeHtml = md.utils.escapeHtml

/** 代码块：语言标签 + 复制按钮 + 高亮 */
md.renderer.rules.fence = (tokens, idx) => {
  const token = tokens[idx]
  const info = token.info ? token.info.trim().split(/\s+/)[0] : ''
  const lang = info.replace(/[^a-zA-Z0-9_-]/g, '').toLowerCase()
  let highlighted: string

  if (lang && hljs.getLanguage(lang)) {
    try {
      highlighted = hljs.highlight(token.content, { language: lang, ignoreIllegals: true }).value
    } catch {
      highlighted = escapeHtml(token.content)
    }
  } else {
    highlighted = escapeHtml(token.content)
  }

  const label = info ? escapeHtml(info) : 'text'
  return `<div class="code-block">
  <div class="code-head">
    <span class="code-lang">${label}</span>
    <button class="code-copy" type="button" data-copy-code>复制</button>
  </div>
  <pre class="hljs"><code class="language-${escapeHtml(lang)}">${highlighted}</code></pre>
</div>`
}

/** 链接统一新窗口打开 */
md.renderer.rules.link_open = (tokens, idx, options, _env, self) => {
  tokens[idx].attrSet('target', '_blank')
  tokens[idx].attrSet('rel', 'noopener noreferrer')
  return self.renderToken(tokens, idx, options)
}

/** 图片懒加载，避免长回答一次拉满网络 */
md.renderer.rules.image = (tokens, idx, options, _env, self) => {
  tokens[idx].attrSet('loading', 'lazy')
  tokens[idx].attrSet('decoding', 'async')
  return self.renderToken(tokens, idx, options)
}

export function renderMarkdown(content: string): string {
  return md.render(content ?? '')
}
