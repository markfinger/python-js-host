module.exports = {
	port: 56789,
	services: [{
		name: 'echo',
		handler: function (data, done) {
			if (!data.echo) {
				return done(new Error('No `echo` prop provided'));
			}
			done(null, data.echo);
		}
	}, {
		name: 'echo-data',
		handler: function (data, done) {
			done(null, JSON.stringify(data));
		}
	}, {
		name: 'error',
		handler: function (data, done) {
			done(new Error('Hello from error service'));
		}
	}, {
		name: 'async-echo',
		handler: function (data, done) {
			setTimeout(function() {
				if (!data.echo) {
					return done(new Error('No `echo` prop provided'));
				}
				done(null, data.echo);
			}, 500);
		}
	}]
};