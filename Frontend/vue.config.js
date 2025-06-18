module.exports = {
  devServer: {
    proxy: {
      '/auth': {
        target: 'http://localhost:5000', // URL del servizio Authentication
        changeOrigin: true
      },
      '/assignments': {
        target: 'http://localhost:5001', // URL del servizio Assignment
        changeOrigin: true
      },
      '/api': {
        target: 'http://localhost:5002', // URL del servizio Submission
        changeOrigin: true,
        pathRewrite: {
          '^/api': ''
        }
      },
      '/submissions': {
        target: 'http://localhost:5002',
        changeOrigin: true
      }
    }
  }
};
