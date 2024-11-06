const { defineConfig } = require('@vue/cli-service');
const webpack = require('webpack');

module.exports = defineConfig({
  transpileDependencies: true,

  publicPath: '/static/dist/',
  outputDir: '../backend/static/dist',

  configureWebpack: {
    resolve: {
      fallback: { https: false, zlib: false, http: false, url: false },
    },
    plugins: [
      new webpack.DefinePlugin({
        __VUE_PROD_HYDRATION_MISMATCH_DETAILS__: JSON.stringify(false),
      }),
      new webpack.ProvidePlugin({
        adapter: ['webrtc-adapter', 'default']
      })
    ],
    module: {
      rules: [
        {
          test: require.resolve('janus-gateway'),
          loader: 'exports-loader',
          options: {
            exports: 'Janus',
          },
        }
      ]
    }
  },

  pluginOptions: {
    vuetify: {
      // Options for Vuetify loader (if any)
    }
  }
})
