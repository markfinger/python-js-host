module.exports = {
	services: [{
		name: 'hello-world',
		handler: function(data, cb) {
			if (!data.name) return cb(new Error('Missing `name` from data'));

			cb(null, 'hello, ' + data.name);
		}
	}]
};