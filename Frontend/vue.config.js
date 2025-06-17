const { defineConfig } = require('@vue/cli-service')

module.exports = defineConfig({
  transpileDependencies: true,
  
  devServer: {
    proxy: {
      '^/api': {
        target: 'http://localhost:8080', // esempio: backend locale
        changeOrigin: true,
        pathRewrite: { '^/api': '/api' }
      }
    }
  }
})
