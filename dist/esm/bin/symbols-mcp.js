#!/usr/bin/env node
const g=require("fs"),f=require("path"),w=require("readline"),R=require("https"),E=require("http");(()=>{const n=process.argv.slice(2);if(!n.length)return;const e=n[0];if(e.startsWith("-"))return;const t={"init-rules":f.join(__dirname,"symbols-mcp-init-rules"),"symbols-mcp-init-rules":f.join(__dirname,"symbols-mcp-init-rules"),audit:f.join(__dirname,"symbols-audit"),"symbols-audit":f.join(__dirname,"symbols-audit")}[e];if(!t)return;g.existsSync(t)||(process.stderr.write(`\u2717 subcommand target missing: ${t}
`),process.exit(2));const s=require("node:child_process").spawnSync("node",[t,...n.slice(1)],{stdio:"inherit"});process.exit(s.status===null?1:s.status)})();const _=f.join(__dirname,"..","symbols_mcp","skills"),I=process.env.SYMBOLS_API_URL||"https://api.symbols.app";function b(n){const e=f.join(_,n);return g.existsSync(e)?g.readFileSync(e,"utf8"):`Skill '${n}' not found`}function $(){const n=f.join(_,"AGENT_INSTRUCTIONS.md");return g.existsSync(n)?g.readFileSync(n,"utf8"):b("CLAUDE.md")}function C(n,e=3){const o=n.toLowerCase().split(/\s+/).filter(s=>s.length>2);o.length||o.push(n.toLowerCase());const t=[];for(const s of g.readdirSync(_)){if(!s.endsWith(".md"))continue;const i=g.readFileSync(f.join(_,s),"utf8");if(!o.some(c=>i.toLowerCase().includes(c)))continue;const r=i.split(`
`);for(let c=0;c<r.length;c++)if(o.some(l=>r[c].toLowerCase().includes(l))){t.push({file:s,snippet:r.slice(Math.max(0,c-2),Math.min(r.length,c+20)).join(`
`)});break}if(t.length>=e)break}return t.length?JSON.stringify(t,null,2):`No results found for '${n}'`}const T="To authenticate, provide one of:\n- **token**: JWT from `smbls login` (stored in ~/.smblsrc) or env var SYMBOLS_TOKEN\n- **api_key**: API key (sk_live_...) from your project's integration settings\n\nTo get a token:\n1. Run `smbls login` in your terminal, or\n2. Use the `login` tool with your email and password";function y(n,e,{token:o,apiKey:t,body:s}={}){return new Promise((i,r)=>{const c=new URL(I+e),l=c.protocol==="https:",a={hostname:c.hostname,port:c.port||(l?443:80),path:c.pathname+c.search,method:n,headers:{"Content-Type":"application/json"}};t?a.headers.Authorization=`ApiKey ${t}`:o&&(a.headers.Authorization=`Bearer ${o}`);const p=s?JSON.stringify(s):null;p&&(a.headers["Content-Length"]=Buffer.byteLength(p));const d=(l?R:E).request(a,u=>{let m="";u.on("data",S=>{m+=S}),u.on("end",()=>{try{i(JSON.parse(m))}catch{i({success:!1,error:`HTTP ${u.statusCode}`,message:m})}})});d.on("error",u=>r(u)),d.setTimeout(3e4,()=>{d.destroy(),r(new Error("Request timeout"))}),p&&d.write(p),d.end()})}function v(n,e){return!n&&!e?`Authentication required.

${T}`:null}async function x(n,e,o){if(!n)return{id:"",error:"Project identifier is required."};if(n.startsWith("pr_")||!/^[0-9a-f]+$/.test(n)){const s=await y("GET",`/core/projects/key/${n}`,{token:e,apiKey:o});return s.success?{id:s.data?._id||"",error:null}:{id:"",error:`Project '${n}' not found: ${s.error||"unknown error"}`}}return{id:n,error:null}}const M=["components","pages","snippets","functions","methods","designSystem","state","dependencies","files","config"],L=new Set(["components","pages","functions","methods","snippets"]);function j(n,e){if(e>=n.length)return-1;let o=e;for(;o<n.length&&` 	
\r`.includes(n[o]);)o++;if(o>=n.length||!"{[".includes(n[o]))return-1;const t=n[o],s=t==="{"?"}":"]";let i=1;o++;let r=null,c=!1,l=!1;for(;o<n.length&&i>0;){const a=n[o];if(l){l=!1,o++;continue}if(a==="\\"){l=!0,o++;continue}if(r){a===r&&(r=null),o++;continue}if(c){a==="`"&&(c=!1),o++;continue}a==="'"||a==='"'?r=a:a==="`"?c=!0:a===t?i++:a===s&&i--,o++}return i===0?o:-1}function A(n){const e={},o=n.replace(/^\s*import\s+.*$/gm,""),t=o.trim();if(t.startsWith("{"))try{return JSON.parse(t)}catch{}const s=/export\s+const\s+(\w+)\s*=\s*/g;let i;const r=[];for(;(i=s.exec(o))!==null;)r.push(i);for(const c of r){const l=c[1],a=c.index+c[0].length,p=j(o,a);p!==-1&&(e[l]=o.slice(a,p).trim())}if(!r.length){const c=/export\s+default\s+/.exec(o);if(c){const l=c.index+c[0].length,a=j(o,l);a!==-1&&(e.__default__=o.slice(l,a).trim())}}return e}function P(n){let e=n.trim();e=B(e),e=F(e),e=e.replace(/(?<=[\{,\n])\s*([a-zA-Z_$][\w$]*)\s*:/g,' "$1":'),e=e.replace(/(?<=[\{,\n])\s*(@[\w$]+)\s*:/g,' "$1":'),e=e.replace(/,\s*([}\]])/g,"$1");try{return JSON.parse(e)}catch{return e}}function B(n){const e=[];let o=0;for(;o<n.length;){const t=n.slice(o),s=t.match(/^(\([^)]*\)\s*=>|\w+\s*=>)\s*/),i=t.match(/^function\s*\w*\s*\(/);if(s&&O(n,o)){const r=D(n,o,!0);if(r>o){e.push(JSON.stringify(n.slice(o,r).trim())),o=r;continue}}if(i&&O(n,o)){const r=D(n,o,!1);if(r>o){e.push(JSON.stringify(n.slice(o,r).trim())),o=r;continue}}e.push(n[o]),o++}return e.join("")}function O(n,e){let o=e-1;for(;o>=0&&` 	
\r`.includes(n[o]);)o--;return o>=0&&":=,[".includes(n[o])}function D(n,e,o){let t=e;if(o){const s=n.indexOf("=>",t);if(s===-1)return-1;for(t=s+2;t<n.length&&` 	
\r`.includes(n[t]);)t++;if(t<n.length&&n[t]==="{")return j(n,t);let i=0;for(;t<n.length;){const r=n[t];if("({[".includes(r))i++;else if(")}]".includes(r)){if(i===0)return t;i--}else if(r===","&&i===0)return t;t++}return t}else{const s=n.indexOf("{",t);return s===-1?-1:j(n,s)}}function F(n){const e=[];let o=0;for(;o<n.length;)if(n[o]==="'"){let t=o+1;for(;t<n.length;){if(n[t]==="\\"&&t+1<n.length){t+=2;continue}if(n[t]==="'")break;t++}const s=n.slice(o+1,t).replace(/"/g,'\\"');e.push(`"${s}"`),o=t+1}else if(n[o]==='"'){let t=o+1;for(;t<n.length;){if(n[t]==="\\"&&t+1<n.length){t+=2;continue}if(n[t]==='"')break;t++}e.push(n.slice(o,t+1)),o=t+1}else e.push(n[o]),o++;return e.join("")}function U(n){return n.replace(/\n/g,"/////n").replace(/`/g,"/////tilde")}function J(n,e,o){const t=typeof o=="string"?o:JSON.stringify(o,null,2),s={title:e,key:e,type:n,code:U(`export default ${t}`)};return(n==="components"||n==="pages")&&Object.assign(s,{settings:{gridOptions:{}},props:{},interactivity:[],dataTypes:[],error:null}),s}function K(n){const e=[],o=[],t=[];for(const[s,i]of Object.entries(n)){if(!M.includes(s))continue;if(typeof i!="object"||i===null||Array.isArray(i)){e.push(["update",[s],i]),o.push(["update",[s],i]);continue}const r=[];for(const[c,l]of Object.entries(i)){const a=[s,c];if(e.push(["update",a,l]),r.push(c),typeof l=="object"&&l!==null&&!Array.isArray(l)){const p=[];for(const[d,u]of Object.entries(l))o.push(["update",[...a,d],u]),p.push(d);p.length&&t.push({path:a,keys:p})}else o.push(["update",a,l]);if(L.has(s)){const p=J(s,c,l),d=["schema",s,c];e.push(["update",d,p]),o.push(["delete",[...d,"code"]]);for(const[u,m]of Object.entries(p))o.push(["update",[...d,u],m])}}r.length&&t.push({path:[s],keys:r})}return{changes:e,granular:o,orders:t}}const G=[[/\bextend\s*:/g,"v2 syntax: use 'extends' (plural) instead of 'extend'"],[/\bchildExtend\s*:/g,"v2 syntax: use 'childExtends' (plural) instead of 'childExtend'"],[/\bon\s*:\s*\{/g,"v2 syntax: flatten event handlers with onX prefix (e.g. onClick) instead of on: {} wrapper"],[/\bprops\s*:\s*\{(?!\s*\})/g,"v2 syntax: flatten props directly on the component instead of props: {} wrapper"]],Q=[[/\bimport\s+.*\bfrom\s+['"]\.\//,"FORBIDDEN: No imports between project files \u2014 reference components by PascalCase key name"],[/\bexport\s+default\s+\{/,"Components should use named exports (export const Name = {}), not default exports"],[/\bfunction\s+\w+\s*\(.*\)\s*\{[\s\S]*?return\s*\{/,"Components must be plain objects, not functions that return objects"],[/\bextends\s*:\s*(?!['"])\w+/,"FORBIDDEN: extends must be a quoted string name (extends: 'Name'), not a variable reference \u2014 register in components/ and use string lookup (Rule 10)"],[/extends\s*:\s*['"]Flex['"]/,"Replace extends: 'Flex' with flow: 'x' or flow: 'y' \u2014 do NOT just remove it, the element needs flow to stay flex (Rule 26)"],[/extends\s*:\s*['"]Box['"]/,"Remove extends: 'Box' \u2014 every element is already a Box (Rule 26)"],[/extends\s*:\s*['"]Text['"]/,"Remove extends: 'Text' \u2014 any element with text: is already Text (Rule 26)"],[/\bchildExtends\s*:\s*\{/,"FORBIDDEN: childExtends must be a quoted string name, not an inline object \u2014 register as a named component (Rule 10)"],[/(?:padding|margin|gap|width|height|fontSize|borderRadius|minWidth|maxWidth|minHeight|maxHeight|top|left|right|bottom|letterSpacing|lineHeight|borderWidth|outlineWidth)\s*:\s*['"]?\d+(?:\.\d+)?px/,"FORBIDDEN: No raw px values \u2014 use design system tokens (A, B, C, etc.) instead of hardcoded pixels (Rule 28)"],[/(?:color|background|backgroundColor|borderColor|fill|stroke)\s*:\s*['"]#[0-9a-fA-F]/,"Use design system color tokens (primary, secondary, white, gray.5) instead of hardcoded hex colors (Rule 27)"],[/(?:color|background|backgroundColor|borderColor|fill|stroke)\s*:\s*['"]rgb/,"Use design system color tokens instead of hardcoded rgb/rgba values (Rule 27)"],[/(?:color|background|backgroundColor|borderColor|fill|stroke)\s*:\s*['"]hsl/,"Use design system color tokens instead of hardcoded hsl/hsla values (Rule 27)"],[/<svg[\s>]/,"FORBIDDEN: Use the Icon component for SVG icons \u2014 store SVGs in designSystem/icons, never inline (Rule 29)"],[/tag\s*:\s*['"]svg['"]/,"FORBIDDEN: Never use tag: 'svg' \u2014 store SVGs in designSystem/icons and use Icon component (Rule 29)"],[/tag\s*:\s*['"]path['"]/,"FORBIDDEN: Never use tag: 'path' \u2014 store SVG paths in designSystem/icons and use Icon component (Rule 29)"],[/extends\s*:\s*['"]Svg['"]/,"Use Icon component for icons, not Svg \u2014 Svg is only for decorative/structural SVGs (Rule 29)"],[/\biconName\s*:/,"FORBIDDEN: Use icon: not iconName: \u2014 the prop is icon: 'name' matching a key in designSystem/icons (Rule 29)"],[/document\.createElement\b/,"FORBIDDEN: No direct DOM manipulation \u2014 use DOMQL declarative object syntax instead (Rule 30)"],[/\.querySelector\b/,"FORBIDDEN: No DOM queries \u2014 reference elements by key name in the DOMQL object tree (Rule 30)"],[/\.appendChild\b/,"FORBIDDEN: No direct DOM manipulation \u2014 nest children as object keys or use children array (Rule 30)"],[/\.removeChild\b/,"FORBIDDEN: No direct DOM manipulation \u2014 use if: (el, s) => condition to show/hide (Rule 30)"],[/\.insertBefore\b/,"FORBIDDEN: No direct DOM manipulation \u2014 use children array ordering (Rule 30)"],[/\.innerHTML\s*=/,"FORBIDDEN: No direct DOM manipulation \u2014 use text: or html: prop (Rule 30)"],[/\.classList\./,"FORBIDDEN: No direct class manipulation \u2014 use isX + '.isX' pattern (Rule 19/30)"],[/\.setAttribute\b/,"FORBIDDEN: No direct DOM manipulation \u2014 set attributes at root level in DOMQL (Rule 30)"],[/\.addEventListener\b/,"FORBIDDEN: No direct event binding \u2014 use onX props: onClick, onInput, etc. (Rule 30)"],[/\.style\.\w+\s*=/,"FORBIDDEN: No direct style manipulation \u2014 use DOMQL CSS-in-props (Rule 30)"],[/html\s*:\s*\(?.*\)?\s*=>\s*/,"FORBIDDEN: Never use html: as a function returning markup \u2014 use DOMQL children, nesting, text:, and if: instead (Rule 31)"],[/return\s*`<\w+/,"FORBIDDEN: Never return HTML template literals \u2014 use DOMQL declarative children and nesting (Rule 31)"],[/style\s*=\s*['"`]/,"FORBIDDEN: No inline style= strings in html \u2014 use DOMQL CSS-in-props (Rule 31)"],[/window\.innerWidth/,"FORBIDDEN: No window.innerWidth checks \u2014 use @mobileL, @tabletS responsive breakpoints (Rule 31)"],[/\.parentNode\b/,"FORBIDDEN: No DOM traversal \u2014 use state and reactive props instead of walking the DOM tree (Rule 32)"],[/\.childNodes\b/,"FORBIDDEN: No DOM traversal \u2014 use state-driven children with if: props (Rule 32)"],[/\.textContent\b/,"FORBIDDEN: No DOM property access \u2014 use state and text: prop (Rule 32)"],[/Array\.from\(\w+\.children\)/,"FORBIDDEN: No DOM child iteration \u2014 use state arrays with children/childExtends and if: filtering (Rule 32)"],[/\.style\.display\s*=/,"FORBIDDEN: No style.display toggling \u2014 use show:/hide: to toggle visibility or if: to remove from DOM (Rule 32)"],[/\.style\.cssText\s*=/,"FORBIDDEN: No direct cssText \u2014 use DOMQL CSS-in-props (Rule 32)"],[/\.dataset\./,"FORBIDDEN: No dataset manipulation \u2014 use state and attr: for data-* attributes (Rule 32)"],[/\.remove\(\)/,"FORBIDDEN: No DOM node removal \u2014 use if: (el, s) => condition to conditionally render (Rule 32)"],[/el\.node\.\w+\s*=/,"FORBIDDEN: No direct el.node property assignment \u2014 use DOMQL props (placeholder:, value:, text:, etc.). Reading el.node is fine (Rule 39), writing is not (Rule 32)"],[/document\.getElementById\b/,"FORBIDDEN: No document.getElementById \u2014 use el.lookdown('key') to find DOMQL elements (Rule 40)"],[/document\.querySelectorAll\b/,"FORBIDDEN: No document.querySelectorAll \u2014 use el.lookdownAll('key') to find DOMQL elements (Rule 40)"],[/el\.parent\.state\b/,"FORBIDDEN: Never use el.parent.state \u2014 with childrenAs: 'state', use s.field directly (Rule 36)"],[/el\.context\.designSystem\b/,"FORBIDDEN: Never read designSystem from el.context in props \u2014 use token strings directly (Rule 38)"],[/^const\s+\w+\s*=\s*(?:\(|function)/m,"FORBIDDEN: No module-level helper functions \u2014 move to functions/ and call via el.call('fnName') (Rule 33)"],[/^let\s+\w+\s*=/m,"FORBIDDEN: No module-level variables \u2014 use el.scope for local state, functions/ for helpers (Rule 33)"],[/^var\s+\w+\s*=/m,"FORBIDDEN: No module-level variables \u2014 use el.scope for local state, functions/ for helpers (Rule 33)"]];function V(n){const e=[],o=[];for(const[i,r]of G){const c=new RegExp(i.source,i.flags);let l;for(;(l=c.exec(n))!==null;){const a=n.slice(0,l.index).split(`
`).length;e.push({line:a,severity:"error",message:r})}}for(const[i,r]of Q){const c=new RegExp(i.source,i.flags||"g");let l;for(;(l=c.exec(n))!==null;){const a=n.slice(0,l.index).split(`
`).length,p=r.includes("FORBIDDEN")?"error":"warning";(p==="error"?e:o).push({line:a,severity:p,message:r})}}const t=e.length+o.length,s=Math.max(1,10-t);return{passed:e.length===0,score:s,violations:e,warnings:o,summary:`${e.length} errors, ${o.length} warnings \u2014 compliance score: ${s}/10`}}const q=[{name:"get_project_rules",description:"ALWAYS call this first before any generate_* tool. Returns the mandatory Symbols.app rules that MUST be followed. Violations cause silent failures \u2014 black page, nothing renders.",inputSchema:{type:"object",properties:{}}},{name:"search_symbols_docs",description:"Search the Symbols documentation knowledge base for relevant information including CLI commands, SDK services, syntax, components, and more.",inputSchema:{type:"object",properties:{query:{type:"string",description:"Natural language search query about Symbols/DOMQL/CLI/SDK"},max_results:{type:"number",description:"Maximum number of results (1-5)",default:3}},required:["query"]}},{name:"get_cli_reference",description:"Returns the complete Symbols CLI (@symbo.ls/cli) command reference \u2014 all smbls commands, options, and workflows.",inputSchema:{type:"object",properties:{}}},{name:"get_sdk_reference",description:"Returns the complete Symbols SDK (@symbo.ls/sdk) API reference \u2014 all services, methods, and usage examples.",inputSchema:{type:"object",properties:{}}},{name:"generate_component",description:"Generate a Symbols.app DOMQL v3 component from a description with full context (rules, syntax, cookbook, default library).",inputSchema:{type:"object",properties:{description:{type:"string",description:"What the component should do and look like"},component_name:{type:"string",description:"PascalCase name for the component",default:"MyComponent"}},required:["description"]}},{name:"generate_page",description:"Generate a Symbols.app page with routing integration and full context.",inputSchema:{type:"object",properties:{description:{type:"string",description:"What the page should contain and do"},page_name:{type:"string",description:"camelCase name for the page",default:"home"}},required:["description"]}},{name:"convert_react",description:"Convert React/JSX code to Symbols.app DOMQL v3 with migration context.",inputSchema:{type:"object",properties:{source_code:{type:"string",description:"The React/JSX source code to convert"}},required:["source_code"]}},{name:"convert_html",description:"Convert raw HTML/CSS to Symbols.app DOMQL v3 components with full context.",inputSchema:{type:"object",properties:{source_code:{type:"string",description:"The HTML/CSS source code to convert"}},required:["source_code"]}},{name:"detect_environment",description:"Detect project type (local, CDN, JSON runtime, or remote server) based on project indicators.",inputSchema:{type:"object",properties:{has_symbols_json:{type:"boolean",default:!1},has_symbols_dir:{type:"boolean",default:!1},has_package_json:{type:"boolean",default:!1},has_cdn_import:{type:"boolean",default:!1},has_iife_script:{type:"boolean",default:!1},has_json_data:{type:"boolean",default:!1},has_mermaid_config:{type:"boolean",default:!1},file_list:{type:"string",description:"Comma-separated list of key files",default:""}}}},{name:"audit_component",description:"Audit a Symbols/DOMQL component for v3 compliance \u2014 checks for v2 syntax, raw px values, hardcoded colors, direct DOM manipulation, and more. Returns violations, warnings, and a score.",inputSchema:{type:"object",properties:{component_code:{type:"string",description:"The JavaScript component code to audit"}},required:["component_code"]}},{name:"convert_to_json",description:"Convert DOMQL v3 JavaScript source code to platform JSON format. Parses export statements, stringifies functions, outputs JSON ready for save_to_project.",inputSchema:{type:"object",properties:{source_code:{type:"string",description:"JavaScript source code with export const/default statements"},section:{type:"string",description:"Target section: components, pages, functions, snippets, designSystem, state",default:"components"}},required:["source_code"]}},{name:"login",description:"Log in to the Symbols platform and get an access token for project operations.",inputSchema:{type:"object",properties:{email:{type:"string",description:"Symbols account email address"},password:{type:"string",description:"Symbols account password"}},required:["email","password"]}},{name:"list_projects",description:"List the user's Symbols projects (names, keys, IDs) to choose from.",inputSchema:{type:"object",properties:{token:{type:"string",description:"JWT access token from login"},api_key:{type:"string",description:"API key (sk_live_...)"}}}},{name:"create_project",description:"Create a new Symbols project on the platform.",inputSchema:{type:"object",properties:{name:{type:"string",description:"Project display name"},key:{type:"string",description:"Project key (pr_xxxx format). Auto-generated if empty"},token:{type:"string",description:"JWT access token from login"},api_key:{type:"string",description:"API key (sk_live_...)"},visibility:{type:"string",description:"private, public, or password-protected",default:"private"}},required:["name"]}},{name:"get_project",description:"Get a project's current data (components, pages, design system, state).",inputSchema:{type:"object",properties:{project:{type:"string",description:"Project key (pr_xxxx) or project ID"},token:{type:"string",description:"JWT access token from login"},api_key:{type:"string",description:"API key (sk_live_...)"},branch:{type:"string",description:"Branch to read from",default:"main"}},required:["project"]}},{name:"save_to_project",description:"Save components/pages/data to a Symbols project. Creates a new version with change tuples, granular changes, orders, and auto-generated schema entries (mirrors CLI push pipeline).",inputSchema:{type:"object",properties:{project:{type:"string",description:"Project key (pr_xxxx) or project ID"},changes:{type:"string",description:"JSON string with project data: { components: {...}, pages: {...}, designSystem: {...}, state: {...}, functions: {...} }"},token:{type:"string",description:"JWT access token from login"},api_key:{type:"string",description:"API key (sk_live_...)"},message:{type:"string",description:"Version commit message"},branch:{type:"string",description:"Branch to save to",default:"main"}},required:["project","changes"]}},{name:"publish",description:"Publish a version of a Symbols project. Makes the specified version (or latest) the published/live version.",inputSchema:{type:"object",properties:{project:{type:"string",description:"Project key (pr_xxxx) or project ID"},token:{type:"string",description:"JWT access token from login"},api_key:{type:"string",description:"API key (sk_live_...)"},version:{type:"string",description:"Version string or ID. Empty for latest"},branch:{type:"string",description:"Branch to publish from",default:"main"}},required:["project"]}},{name:"push",description:"Deploy a Symbols project to an environment (production, staging, dev).",inputSchema:{type:"object",properties:{project:{type:"string",description:"Project key (pr_xxxx) or project ID"},token:{type:"string",description:"JWT access token from login"},api_key:{type:"string",description:"API key (sk_live_...)"},environment:{type:"string",description:"Target environment key",default:"production"},mode:{type:"string",description:"Deploy mode: latest, published, version, or branch",default:"published"},version:{type:"string",description:'Version string when mode is "version"'},branch:{type:"string",description:'Branch when mode is "latest" or "branch"',default:"main"}},required:["project"]}}];async function W(n,e){if(n==="get_project_rules")return $();if(n==="search_symbols_docs")return C(e.query,e.max_results||3);if(n==="get_cli_reference")return b("CLI.md");if(n==="get_sdk_reference")return b("SDK.md");function o(...t){return t.map(s=>b(s)).filter(s=>!s.startsWith("Skill ")).join(`

---

`)}if(n==="generate_component"){const t=e.component_name||"MyComponent",s=o("RULES.md","COMMON_MISTAKES.md","COMPONENTS.md","SYNTAX.md","COOKBOOK.md","DEFAULT_PROJECT.md");return`# Generate Component: ${t}

## Description
${e.description}

## Requirements
- Named export: \`export const ${t} = { ... }\`
- DOMQL v3 syntax only (extends, childExtends, flattened props, onX events)
- **MANDATORY: ALL values MUST use design system tokens** \u2014 spacing (A, B, C, D), colors (primary, surface, white, gray.5), typography (fontSize: 'B'). ZERO px values, ZERO hex colors, ZERO rgb/hsl.
- NO imports between files \u2014 PascalCase keys auto-extend registered components
- Include responsive breakpoints where appropriate (@tabletS, @mobileL)
- Use the default library components (Button, Avatar, Icon, Field, etc.) via extends
- Use Icon component for SVGs \u2014 store icons in designSystem/icons
- NO direct DOM manipulation \u2014 all structure via DOMQL declarative syntax
- Follow modern UI/UX: visual hierarchy, confident typography, minimal cognitive load

## Context \u2014 Rules, Syntax & Examples

${s}`}if(n==="generate_page"){const t=e.page_name||"home",s=o("RULES.md","COMMON_MISTAKES.md","PROJECT_STRUCTURE.md","SHARED_LIBRARIES.md","PATTERNS.md","SNIPPETS.md","DEFAULT_PROJECT.md","COMPONENTS.md");return`# Generate Page: ${t}

## Description
${e.description}

## Requirements
- Export as: \`export const ${t} = { ... }\`
- Page is a plain object composing components
- Add to pages/index.js route map: \`'/${t}': ${t}\`
- Use components by PascalCase key (Header, Footer, Hero, etc.)
- **MANDATORY: ALL values MUST use design system tokens** \u2014 spacing (A, B, C, D), colors (primary, surface, white, gray.5), typography (fontSize: 'B'). ZERO px values, ZERO hex colors, ZERO rgb/hsl.
- Use Icon component for SVGs \u2014 store icons in designSystem/icons
- NO direct DOM manipulation \u2014 all structure via DOMQL declarative syntax
- Include responsive layout adjustments

## Context \u2014 Rules, Structure, Patterns & Snippets

${s}`}if(n==="convert_react"){const t=o("RULES.md","MIGRATION.md","SYNTAX.md","COMPONENTS.md","LEARNINGS.md");return`# Convert React \u2192 Symbols DOMQL v3

## Source Code to Convert
\`\`\`jsx
${e.source_code}
\`\`\`

## Conversion Rules
- Function/class components \u2192 plain object exports
- JSX \u2192 nested object children (PascalCase keys auto-extend)
- import/export between files \u2192 REMOVE (reference by key name)
- useState \u2192 state: { key: val } + s.update({ key: newVal })
- useEffect \u2192 onRender (mount), onStateUpdate (deps)
- props \u2192 flattened directly on component (no props wrapper)
- onClick={handler} \u2192 onClick: (event, el, state) => {}
- className \u2192 use design tokens and theme directly
- map() \u2192 children: (el, s) => s.items, childExtends, childProps
- conditional rendering \u2192 if: (el, s) => boolean
- CSS modules/styled \u2192 CSS-in-props with design tokens
- React.Fragment \u2192 not needed, just nest children

## Context \u2014 Migration Guide, Syntax & Rules

${t}`}if(n==="convert_html"){const t=o("RULES.md","SYNTAX.md","COMPONENTS.md","DESIGN_SYSTEM.md","SNIPPETS.md","LEARNINGS.md");return`# Convert HTML \u2192 Symbols DOMQL v3

## Source Code to Convert
\`\`\`html
${e.source_code}
\`\`\`

## Conversion Rules
- <div> \u2192 Box, Flex, or Grid (based on layout purpose)
- <span>, <p>, <h1>-<h6> \u2192 Text, P, H with tag property
- <a> \u2192 Link (has built-in SPA router)
- <button> \u2192 Button (has icon/text support)
- <input> \u2192 Input, Radio, Checkbox (based on type)
- <img> \u2192 Img
- <form> \u2192 Form (extends Box with tag: 'form')
- <ul>/<ol> + <li> \u2192 children array with childExtends
- CSS classes \u2192 flatten as CSS-in-props on the component
- CSS px values \u2192 design tokens (16px \u2192 'A', 26px \u2192 'B', 42px \u2192 'C')
- CSS colors \u2192 theme color tokens
- media queries \u2192 @tabletS, @mobileL, @screenS breakpoints
- id/class attributes \u2192 not needed (use key names and themes)
- inline styles \u2192 flatten as component properties
- <style> blocks \u2192 distribute to component-level properties

## Context \u2014 Syntax, Components & Design System

${t}`}if(n==="detect_environment"){let t="unknown",s="low";if(e.has_mermaid_config)t="remote_server",s="high";else if(e.has_json_data)t="json_runtime",s="high";else if(e.has_symbols_json&&e.has_symbols_dir)t="local_project",s="high";else if(e.has_symbols_dir||e.has_package_json&&e.has_symbols_json)t="local_project",s="medium";else if(e.has_cdn_import||e.has_iife_script)t="cdn",s="high";else if(e.has_package_json)t="local_project",s="low";else if(e.file_list){const c=e.file_list.toLowerCase();c.includes("index.html")&&!c.includes("package.json")&&!c.includes("symbols.json")&&(t="cdn",s="medium")}const i=b("RUNNING_APPS.md"),r=t==="local_project"?`

## Shared Libraries

`+b("SHARED_LIBRARIES.md"):"";return`# Environment Detection

**Detected: ${t}** (confidence: ${s})

${i}${r}`}if(n==="audit_component"){const t=V(e.component_code),s=b("AUDIT.md");let i=`# Audit Report

## Summary
${t.summary}
Passed: ${t.passed?"Yes":"No"}

## Violations (Errors)
`;if(t.violations.length)for(const r of t.violations)i+=`- **Line ${r.line}**: ${r.message}
`;else i+=`No violations found.
`;if(i+=`
## Warnings
`,t.warnings.length)for(const r of t.warnings)i+=`- **Line ${r.line}**: ${r.message}
`;else i+=`No warnings.
`;return t.violations.length&&(i+=`
## MANDATORY ACTION

**Every violation above MUST be fixed. There is NO concept of "known debt", "accepted violations", or "95% fixed" in Symbols. ALL violations must reach 100% resolution. Do NOT label any violation as "known debt" or defer it. Rewrite the code using proper DOMQL syntax.**

`),i+=`
## Detailed Rules Reference

${s}`,i}if(n==="convert_to_json"){const t=e.section||"components",s=A(e.source_code);if(!Object.keys(s).length)return"Could not parse any exports from the source code. Make sure it contains `export const Name = { ... }` or `export default { ... }`.";const i={};for(const[a,p]of Object.entries(s)){const d=typeof p=="string"?P(p):p;a==="__default__"?["designSystem","state","dependencies","config"].includes(t)?i[t]=d:(i[t]||(i[t]={}),i[t].default=d):(i[t]||(i[t]={}),i[t][a]=d)}const r=JSON.stringify(i,null,2),c=Object.keys(i),l=[];for(const a of c)typeof i[a]=="object"&&i[a]&&l.push(...Object.keys(i[a]));return`# Converted to Platform JSON

**Section:** ${c.join(", ")}
**Items:** ${l.join(", ")||"default export"}

\`\`\`json
${r}
\`\`\`

This JSON is ready to use with \`save_to_project\`. Pass the JSON object above as the \`changes\` parameter.

**Full flow:**
1. \`convert_to_json\` (done) \u2192 structured JSON
2. \`save_to_project\` \u2192 push to platform (creates new version)
3. \`publish\` \u2192 make version live
4. \`push\` \u2192 deploy to environment (production/staging/dev)`}if(n==="login"){const t=await y("POST","/core/auth/login",{body:{email:e.email,password:e.password}});if(t.success){const{tokens:s={},user:i={}}=t.data||{},r=s.accessToken||"";return`Logged in as ${i.name||i.email||"unknown"}.
Token: ${r}
Expires: ${s.accessTokenExp?.expiresAt||"unknown"}

Use this token with project, save, publish and push tools.`}return`Login failed: ${t.error||t.message||"Unknown error"}`}if(n==="list_projects"){const t=v(e.token,e.api_key);if(t)return t;const s=await y("GET","/core/projects",{token:e.token,apiKey:e.api_key});if(s.success){const i=s.data||[];if(!i.length)return"No projects found. Use `create_project` to create one.";const r=[`# Your Projects
`];for(const c of i)r.push(`- **${c.name||"Untitled"}** \u2014 key: \`${c.key||"\u2014"}\`, id: \`${c._id||""}\`, visibility: ${c.visibility||"private"}`);return r.join(`
`)}return`Failed to list projects: ${s.error||"Unknown error"}`}if(n==="create_project"){const t=v(e.token,e.api_key);if(t)return t;const s={name:e.name,visibility:e.visibility||"private",language:"javascript"};e.key&&(s.key=e.key);const i=await y("POST","/core/projects",{token:e.token,apiKey:e.api_key,body:s});if(i.success){const r=i.data||{};return`Project created successfully.
Name: ${r.name||e.name}
Key: \`${r.key||"unknown"}\`
ID: \`${r._id||"unknown"}\`

Use this project key/ID with \`save_to_project\` to push your components.`}return`Create failed: ${i.error||"Unknown error"}
${i.message||""}`}if(n==="get_project"){const t=v(e.token,e.api_key);if(t)return t;const s=e.branch||"main",i=e.project,c=i.startsWith("pr_")||!/^[0-9a-f]+$/.test(i)?`/core/projects/key/${i}/data?branch=${s}&version=latest`:`/core/projects/${i}/data?branch=${s}&version=latest`,l=await y("GET",c,{token:e.token,apiKey:e.api_key});if(l.success){const a=l.data||{},p=a.components||{},d=a.pages||{},u=a.designSystem||{},m=a.state||{},S=a.functions||{},h=[`# Project Data (branch: ${s})
`];return h.push(`**Components (${Object.keys(p).length}):** ${Object.keys(p).slice(0,20).join(", ")||"none"}`),h.push(`**Pages (${Object.keys(d).length}):** ${Object.keys(d).slice(0,20).join(", ")||"none"}`),h.push(`**Design System keys:** ${Object.keys(u).slice(0,15).join(", ")||"none"}`),h.push(`**State keys:** ${Object.keys(m).slice(0,15).join(", ")||"none"}`),h.push(`**Functions (${Object.keys(S).length}):** ${Object.keys(S).slice(0,15).join(", ")||"none"}`),h.push(`
---

Full data:
\`\`\`json
${JSON.stringify(a,null,2).slice(0,8e3)}
\`\`\``),h.join(`
`)}return`Failed to get project data: ${l.error||"Unknown error"}`}if(n==="save_to_project"){const t=v(e.token,e.api_key);if(t)return t;let s;try{s=JSON.parse(e.changes)}catch(m){return`Invalid JSON in changes: ${m.message}`}if(typeof s!="object"||s===null)return"Changes must be a JSON object with keys like components, pages, designSystem, state, functions.";const{id:i,error:r}=await x(e.project,e.token,e.api_key);if(r)return r;const{changes:c,granular:l,orders:a}=K(s);if(!c.length)return"No valid changes found. Include at least one data section.";const p=e.branch||"main",d={changes:c,granularChanges:l,orders:a,message:e.message||"Updated via Symbols MCP",branch:p,type:"patch"},u=await y("POST",`/core/projects/${i}/changes`,{token:e.token,apiKey:e.api_key,body:d});if(u.success){const m=u.data||{},S=m.value||m.version||m.id||"unknown",h=Object.keys(s);return`Saved to project \`${e.project}\` successfully.
Version: ${S}
Branch: ${p}
Sections updated: ${h.join(", ")}

Use \`publish\` to make this version live, or \`push\` to deploy to an environment.`}return`Save failed: ${u.error||"Unknown error"}
${u.message||""}`}if(n==="publish"){const t=v(e.token,e.api_key);if(t)return t;const{id:s,error:i}=await x(e.project,e.token,e.api_key);if(i)return i;const r={branch:e.branch||"main"};e.version&&(r.version=e.version);const c=await y("POST",`/core/projects/${s}/publish`,{token:e.token,apiKey:e.api_key,body:r});if(c.success){const l=c.data||{};return`Published successfully.
Version: ${l.value||l.id||"unknown"}`}return`Publish failed: ${c.error||"Unknown error"}
${c.message||""}`}if(n==="push"){const t=v(e.token,e.api_key);if(t)return t;const{id:s,error:i}=await x(e.project,e.token,e.api_key);if(i)return i;const r=e.environment||"production",c=e.mode||"published",l=e.branch||"main",a={mode:c,branch:l};e.version&&(a.version=e.version);const p=await y("POST",`/core/projects/${s}/environments/${r}/publish`,{token:e.token,apiKey:e.api_key,body:a});if(p.success){const d=p.data||{},u=d.config||{};return`Pushed to ${d.key||r} successfully.
Mode: ${u.mode||c}
Version: ${u.version||"latest"}
Branch: ${u.branch||l}`}return`Push failed: ${p.error||"Unknown error"}
${p.message||""}`}throw new Error(`Unknown tool: ${n}`)}function k(n){process.stdout.write(JSON.stringify(n)+`
`)}async function H(n){if(n.method){if(n.method==="initialize")return k({jsonrpc:"2.0",id:n.id,result:{protocolVersion:n.params?.protocolVersion??"2025-03-26",capabilities:{tools:{}},serverInfo:{name:"Symbols MCP",version:"1.0.15"}}});if(n.method!=="notifications/initialized"){if(n.method==="ping")return k({jsonrpc:"2.0",id:n.id,result:{}});if(n.method==="tools/list")return k({jsonrpc:"2.0",id:n.id,result:{tools:q}});if(n.method==="tools/call"){const{name:e,arguments:o={}}=n.params;try{const t=await W(e,o);return k({jsonrpc:"2.0",id:n.id,result:{content:[{type:"text",text:t}]}})}catch(t){return k({jsonrpc:"2.0",id:n.id,result:{content:[{type:"text",text:t.message}],isError:!0}})}}n.id!==void 0&&k({jsonrpc:"2.0",id:n.id,error:{code:-32601,message:"Method not found"}})}}}const N=w.createInterface({input:process.stdin,terminal:!1});N.on("line",n=>{if(n.trim())try{H(JSON.parse(n)).catch(e=>process.stderr.write(`Handler error: ${e.message}
`))}catch(e){process.stderr.write(`Parse error: ${e.message}
`)}}),N.on("close",()=>process.exit(0));
