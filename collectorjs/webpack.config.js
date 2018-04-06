module.exports = {
  entry: "./conduster.js",
  output: {
    path: __dirname + "/../collector/templates/collector",
    filename: "conduster.js"
  },
  module: {
    loaders: [
      {
        test: /\.js$/,
        exclude: /node_modules/,
        loader: 'babel-loader'
      }
    ]
  }
};