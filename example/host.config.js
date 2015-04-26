// The code that the host loads and runs

var fs = require('fs');

module.exports = {
	functions: {
		hello_world: function(data, cb) {
			if (!data.name) return cb(new Error('No name was provided'));

			cb(null, 'Hello, ' + data.name + '!');
		},
		double: function(data, cb) {
			if (!data.number) return cb(new Error('No number was provided'));

			cb(null, data.number * 2);
		},
		read_file: function(data, cb) {
			if (!data.file) return cb(new Error('No file was provided'));

			fs.readFile(data.file, function(err, contents) {
				if (err) cb(err);

				cb(null, contents.toString());
			});
		}
	}
};