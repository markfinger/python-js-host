// The config file used by the singleton ManagedServiceHost in service_host.host

module.exports = {
	services: {
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
			done(new Error('Hello from error service'));
		},
		async_echo: function(data, done) {
			setTimeout(function() {
				if (!data.echo) {
					return done(new Error('No `echo` prop provided'));
				}
				done(null, data.echo);
			}, 500);
		}
	}
};