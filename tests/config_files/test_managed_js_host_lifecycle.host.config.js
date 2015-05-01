module.exports = {
	port: 23456,
	functions: {
		test: function(data, cb) {
			cb(null, 'test');
		}
	}
};