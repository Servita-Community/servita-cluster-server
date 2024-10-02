const { defineConfig } = require('@vue/cli-service')
module.exports = defineConfig({
  transpileDependencies: true,

  publicPath: './',

  configureWebpack: {
    resolve: {
      fallback: { https: false, zlib: false, http: false, url: false },
    }
  },

  devServer: {
    historyApiFallback: true,
  },

  pluginOptions: {
    vuetify: {
      // https://github.com/vuetifyjs/vuetify-loader/tree/next/packages/vuetify-loader
    }
  }
})
