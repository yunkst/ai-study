import js from "@eslint/js";
import globals from "globals";
import tseslint from "typescript-eslint";
import pluginVue from "eslint-plugin-vue";
import { defineConfig } from "eslint/config";
import openApiValidator from "./eslint-plugin-openapi-validator.js";
import noDirectAxios from "./eslint-plugin-no-direct-axios.js";

export default defineConfig([
  { files: ["**/*.{js,mjs,cjs,ts,mts,cts,vue}"], plugins: { js }, extends: ["js/recommended"], languageOptions: { globals: globals.browser } },
  tseslint.configs.recommended,
  pluginVue.configs["flat/essential"],
  { files: ["**/*.vue"], languageOptions: { parserOptions: { parser: tseslint.parser } } },
  {
    plugins: {
      "openapi-validator": openApiValidator,
      "no-direct-axios": noDirectAxios
    },
    rules: {
      "vue/multi-word-component-names": "off",
      "openapi-validator/validate-api-consistency": "error",
      "no-direct-axios/no-direct-axios": "error"
    }
  }
]);
