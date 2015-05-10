var httpProxy = require('http-proxy');

port = 8000;
target = 30403;

httpProxy.createProxyServer({target:'http://127.0.0.1:' + target}).listen(port);

console.log('proxy listening on port ' + port + ' and proxying to ' + target);