module.exports = {
	port: 30403,
	functions: {
		echo: function(data, done) {
			if (!data.echo) {
				return done(new Error('No `echo` prop provided'));
			}
			done(null, data.echo);
		},
		echo_data: function(data, done) {
			done(null, JSON.stringify(data));
		},
		error: function(data, done) {
			done(new Error('Hello from error function'));
		},
		async_echo: function(data, done) {
			setTimeout(function () {
				if (!data.echo) {
					return done(new Error('No `echo` prop provided'));
				}
				done(null, data.echo);
			}, 500);
		},
		counter: (function() {
			var count = 0;
			return function(data, cb) {
				cb(null, ++count);
			};
		})()
	}
};