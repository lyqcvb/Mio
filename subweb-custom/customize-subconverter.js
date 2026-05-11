const fs = require("fs");

const backendOrigin = process.env.MIO_BACKEND_ORIGIN || "http://39.106.99.222";
const backendUrl = `${backendOrigin.replace(/\/$/, "")}/sub?`;
const directRulesUrl = `${backendOrigin.replace(/\/$/, "")}/direct-rules`;
const remoteConfig = "config/myclash.ini";

function replaceRequired(source, pattern, replacement, label) {
  const next = source.replace(pattern, replacement);
  if (next === source) {
    throw new Error(`Failed to apply customization: ${label}`);
  }
  return next;
}

const viewFile = "src/views/Subconverter.vue";
let view = fs.readFileSync(viewFile, "utf8");

view = replaceRequired(
  view,
  /\n\s*<div style="display: inline-block; position:absolute; right: 20px">\{\{ backendVersion \}\}<\/div>/,
  "",
  "hide backend version header"
);

view = replaceRequired(
  view,
  /\n\s*<el-form-item label="模式设置:">\n\s*<el-radio v-model="advanced" label="1">基础模式<\/el-radio>\n\s*<el-radio v-model="advanced" label="2">进阶模式<\/el-radio>\n\s*<\/el-form-item>/,
  "",
  "remove mode selector"
);

view = replaceRequired(
  view,
  /\n\s*<el-form-item label="后端地址:">[\s\S]*?<\/el-form-item>\n\s*<el-form-item label="远程配置:">[\s\S]*?<\/el-form-item>/,
  "",
  "remove backend and remote config fields"
);

view = replaceRequired(
  view,
  /\n\s*<el-button[\s\S]*?icon="el-icon-upload"[\s\S]*?上传配置\s*<\/el-button>/,
  "",
  "remove upload config button"
);

view = replaceRequired(
  view,
  /\n\s*<el-form-item label-width="0px" style="text-align: center">\n\s*<el-button\n\s*:style="\{ width: '290px' \}"[\s\S]*?从 URL 解析\s*<\/el-button>\n\s*<\/el-form-item>/,
  "",
  "remove parse from URL row"
);

view = replaceRequired(
  view,
  /<el-button\n\s*:style="buttonStyle"\n\s*type="primary"\n\s*@click="clashInstall"\n\s*icon="el-icon-connection"\n\s*:disabled="!canImportClash">\n\s*一键导入 Clash\n\s*<\/el-button>/,
  `<el-button
                  :style="buttonStyle"
                  type="primary"
                  @click="clashInstall"
                  icon="el-icon-connection"
                  :disabled="!canImportClash">
                  一键导入 Clash
                </el-button>
                <el-button
                  :style="buttonStyle"
                  type="primary"
                  @click="openDirectRulesDialog"
                  icon="el-icon-edit">
                  直连规则
                </el-button>`,
  "add direct rules button"
);

view = replaceRequired(
  view,
  /<UrlParseDialog[\s\S]*?\n\s*\/>\n/,
  `<el-dialog
      custom-class="direct-rules-dialog"
      title="编辑规则"
      :visible.sync="dialogDirectRulesVisible"
      width="96vw"
      top="3vh"
      :close-on-click-modal="false">
      <div v-loading="directRulesLoading" class="direct-rules-editor">
        <section class="direct-rule-form">
          <div class="direct-rule-row">
            <label>规则类型</label>
            <el-select v-model="directRuleForm.type" placeholder="规则类型">
              <el-option v-for="item in directRuleTypes" :key="item.value" :label="item.label" :value="item.value"></el-option>
            </el-select>
          </div>
          <div class="direct-rule-row">
            <label>规则内容</label>
            <el-input v-model="directRuleForm.value" placeholder="example.com" @keyup.enter.native="addDirectRule('prepend')"></el-input>
          </div>
          <div class="direct-rule-row">
            <label>代理策略</label>
            <el-select v-model="directRuleForm.policy" placeholder="代理策略">
              <el-option label="直接连接 (DIRECT)" value="国内直连"></el-option>
            </el-select>
          </div>
          <el-button class="direct-rule-add" type="primary" icon="el-icon-top" @click="addDirectRule('prepend')">添加前置规则</el-button>
          <el-button class="direct-rule-add" type="primary" icon="el-icon-bottom" @click="addDirectRule('append')">添加后置规则</el-button>
        </section>
        <section class="direct-rule-list">
          <div class="direct-rule-filter">
            <el-input v-model="directRulesFilter" clearable prefix-icon="el-icon-search" placeholder="过滤条件"></el-input>
          </div>
          <div class="direct-rule-scroll">
            <article v-for="(rule, i) in filteredDirectRuleCards" :key="rule.raw + i" class="direct-rule-card">
              <div>
                <strong>{{ rule.value }}</strong>
                <div class="direct-rule-type">{{ rule.type }}</div>
              </div>
              <span class="direct-rule-policy">DIRECT</span>
              <el-button class="direct-rule-delete" type="text" icon="el-icon-delete-solid" @click="removeDirectRule(rule.raw)"></el-button>
            </article>
            <el-empty v-if="filteredDirectRuleCards.length === 0" description="暂无规则"></el-empty>
          </div>
        </section>
      </div>
      <span slot="footer" class="dialog-footer">
        <el-button @click="dialogDirectRulesVisible = false">取消</el-button>
        <el-button type="primary" :loading="directRulesLoading" @click="saveDirectRules">保存规则</el-button>
      </span>
    </el-dialog>
`,
  "replace URL parse dialog with direct rules dialog"
);

view = view.replace("mounted() {", 'mounted() {\n    this.advanced = "2";');
view = view.replace(
  "this.form.clientType = CONSTANTS.DEFAULT_CLIENT_TYPE;",
  "this.form.clientType = CONSTANTS.DEFAULT_CLIENT_TYPE;"
);
view = view.replace(
  "this.getBackendVersion();",
  "// Hide backend version from the UI and avoid the extra startup request."
);
view = view.replace(
  /\n\s*\/\/ 延迟加载隐私提示，避免阻塞页面初始化\n\s*setTimeout\(\(\) => \{\n\s*this\.notify\(\);\n\s*\}, 1000\);/,
  ""
);

view = replaceRequired(
  view,
  /backendVersion: "",/,
  `backendVersion: "",
      dialogDirectRulesVisible: false,
      directRulesText: "",
      directRules: [],
      directRulesFilter: "",
      directRuleForm: {
        type: "DOMAIN-SUFFIX",
        value: "",
        policy: "国内直连"
      },
      directRuleTypes: [
        { label: "匹配完整域名 (DOMAIN)", value: "DOMAIN" },
        { label: "匹配域名后缀 (DOMAIN-SUFFIX)", value: "DOMAIN-SUFFIX" },
        { label: "匹配域名关键字 (DOMAIN-KEYWORD)", value: "DOMAIN-KEYWORD" },
        { label: "匹配 IP 段 (IP-CIDR)", value: "IP-CIDR" },
        { label: "匹配 IPv6 段 (IP-CIDR6)", value: "IP-CIDR6" }
      ],
      directRulesLoading: false,`,
  "add direct rules state"
);

view = replaceRequired(
  view,
  /canImportClash\(\) \{\n\s*return this\.customSubUrl\.length > 0;\n\s*\},/,
  `canImportClash() {
      return this.customSubUrl.length > 0;
    },

    directRuleCards() {
      return this.directRules.map(rule => this.parseDirectRule(rule));
    },

    filteredDirectRuleCards() {
      const keyword = this.directRulesFilter.trim().toLowerCase();
      if (!keyword) {
        return this.directRuleCards;
      }
      return this.directRuleCards.filter(rule => rule.raw.toLowerCase().includes(keyword));
    },`,
  "add direct rules computed properties"
);

view = replaceRequired(
  view,
  /makeUrlClick\(\) \{\n\s*const url = this\.makeUrl/,
  `makeUrlClick() {
      this.form.customBackend = "${backendUrl}";
      this.form.remoteConfig = "${remoteConfig}";
      const url = this.makeUrl`,
  "force backend and remote config on generate"
);

view = replaceRequired(
  view,
  /\n\s*backendSearch\(queryString, cb\) \{/,
  `
    directRulesEndpoint() {
      return "${directRulesUrl}";
    },

    parseDirectRule(rule) {
      const parts = rule.split(",").map(part => part.trim());
      return {
        raw: rule,
        type: parts[0] || "DOMAIN-SUFFIX",
        value: parts[1] || rule,
        policy: parts[2] || "国内直连"
      };
    },

    syncDirectRulesText() {
      this.directRulesText = this.directRules.join("\\n");
    },

    async openDirectRulesDialog() {
      this.dialogDirectRulesVisible = true;
      this.directRulesLoading = true;
      try {
        const res = await this.$axios.get(this.directRulesEndpoint());
        this.directRules = Array.isArray(res.data.rules) ? res.data.rules : [];
        this.syncDirectRulesText();
      } catch (error) {
        this.$message.error("直连规则读取失败：" + (error.message || error));
      } finally {
        this.directRulesLoading = false;
      }
    },

    makeDirectRule() {
      const value = this.directRuleForm.value.trim();
      if (!value) {
        return "";
      }
      const type = this.directRuleForm.type;
      const suffix = ["IP-CIDR", "IP-CIDR6"].includes(type) ? ",no-resolve" : "";
      return [type, value, this.directRuleForm.policy].join(",") + suffix;
    },

    addDirectRule(position) {
      const rule = this.makeDirectRule();
      if (!rule) {
        this.$message.warning("规则内容不能为空");
        return;
      }
      this.directRules = this.directRules.filter(item => item !== rule);
      if (position === "prepend") {
        this.directRules.unshift(rule);
      } else {
        this.directRules.push(rule);
      }
      this.directRuleForm.value = "";
      this.syncDirectRulesText();
    },

    removeDirectRule(rule) {
      this.directRules = this.directRules.filter(item => item !== rule);
      this.syncDirectRulesText();
    },

    async saveDirectRules() {
      this.directRulesLoading = true;
      try {
        this.syncDirectRulesText();
        const res = await this.$axios.put(this.directRulesEndpoint(), { text: this.directRulesText });
        this.directRules = Array.isArray(res.data.rules) ? res.data.rules : this.directRules;
        this.syncDirectRulesText();
        this.$message.success("直连规则已保存");
        this.dialogDirectRulesVisible = false;
      } catch (error) {
        this.$message.error("直连规则保存失败：" + (error.message || error));
      } finally {
        this.directRulesLoading = false;
      }
    },

    backendSearch(queryString, cb) {`,
  "add direct rules methods"
);

view += `
<style>
.direct-rules-dialog .el-dialog__body {
  padding: 16px 20px;
}

.direct-rules-editor {
  display: grid;
  grid-template-columns: 320px minmax(0, 1fr);
  gap: 18px;
  min-height: 66vh;
}

.direct-rule-form {
  border-right: 1px solid #ebeef5;
  padding-right: 18px;
}

.direct-rule-row {
  margin-bottom: 14px;
}

.direct-rule-row label {
  display: block;
  color: #606266;
  font-size: 13px;
  margin-bottom: 6px;
}

.direct-rule-row .el-select {
  width: 100%;
}

.direct-rule-add {
  width: 100%;
  margin: 0 0 10px 0;
}

.direct-rule-add + .direct-rule-add {
  margin-left: 0;
}

.direct-rule-filter {
  margin-bottom: 12px;
}

.direct-rule-scroll {
  max-height: 60vh;
  overflow: auto;
  padding-right: 4px;
}

.direct-rule-card {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto 32px;
  align-items: center;
  gap: 12px;
  border: 1px solid #ebeef5;
  border-radius: 6px;
  padding: 10px 12px;
  margin-bottom: 8px;
}

.direct-rule-card strong {
  display: block;
  overflow-wrap: anywhere;
}

.direct-rule-type {
  color: #909399;
  font-size: 12px;
  margin-top: 4px;
}

.direct-rule-policy {
  color: #409eff;
  font-size: 12px;
  white-space: nowrap;
}

.direct-rule-delete {
  padding: 0;
}

@media (max-width: 760px) {
  .direct-rules-editor {
    grid-template-columns: 1fr;
  }

  .direct-rule-form {
    border-right: 0;
    border-bottom: 1px solid #ebeef5;
    padding-right: 0;
    padding-bottom: 14px;
  }
}
</style>
`;

fs.writeFileSync(viewFile, view);

const formFile = "src/composables/useSubscriptionForm.js";
let form = fs.readFileSync(formFile, "utf8");
form = form.replace('customBackend: "",', `customBackend: "${backendUrl}",`);
form = form.replace('remoteConfig: "",', `remoteConfig: "${remoteConfig}",`);
fs.writeFileSync(formFile, form);

const constantsFile = "src/config/constants.js";
let constants = fs.readFileSync(constantsFile, "utf8");
constants = constants.replace(
  /DEFAULT_BACKEND: import\.meta\.env\.VITE_SUBCONVERTER_DEFAULT_BACKEND \+ '\/sub\?',/,
  `DEFAULT_BACKEND: "${backendUrl}",`
);
constants = constants.replace(/PROJECT: import\.meta\.env\.VITE_PROJECT,/, 'PROJECT: "https://github.com/Mio",');
fs.writeFileSync(constantsFile, constants);

fs.writeFileSync(
  "src/config/remote-configs.js",
  `export const REMOTE_CONFIGS = [
  {
    label: "Mio",
    options: [
      {
        label: "myclash - 自定义规则",
        value: "${remoteConfig}"
      }
    ]
  }
];
`
);

const viteFile = "vite.config.js";
let vite = fs.readFileSync(viteFile, "utf8");
vite = vite.replace("export default defineConfig({", "export default defineConfig({\n    base: '/subconvert/',");
fs.writeFileSync(viteFile, vite);

const htmlFile = "index.html";
let html = fs.readFileSync(htmlFile, "utf8").replace("<title>sub-web</title>", "<title>Mio</title>");
fs.writeFileSync(htmlFile, html);

const packageFile = "package.json";
const pkg = JSON.parse(fs.readFileSync(packageFile, "utf8"));
pkg.name = "mio";
fs.writeFileSync(packageFile, JSON.stringify(pkg, null, 2) + "\n");
