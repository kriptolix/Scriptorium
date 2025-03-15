pkgdatadir = get_option('prefix') / get_option('datadir') / meson.project_name()
gnome = import('gnome')

desktop_file = i18n.merge_file(
	input: 'com.github.cgueret.Scriptorium.desktop.in',
	output: 'com.github.cgueret.Scriptorium.desktop',
	type: 'desktop',
	po_dir: '../po',
	install: true,
	install_dir: get_option('datadir') / 'applications',
)

desktop_utils = find_program('desktop-file-validate', required: false)
if desktop_utils.found()
	test('Validate desktop file', desktop_utils, args: [desktop_file])
endif

appstream_file = i18n.merge_file(
	input: 'com.github.cgueret.Scriptorium.metainfo.xml.in',
	output: 'com.github.cgueret.Scriptorium.metainfo.xml',
	po_dir: '../po',
	install: true,
	install_dir: get_option('datadir') / 'metainfo',
)

appstreamcli = find_program('appstreamcli', required: false, disabler: true)
test(
	'Validate appstream file',
	appstreamcli,
	args: ['validate', '--no-net', '--explain', appstream_file],
)

install_data(
	'com.github.cgueret.Scriptorium.gschema.xml',
	install_dir: get_option('datadir') / 'glib-2.0' / 'schemas',
)

compile_schemas = find_program('glib-compile-schemas', required: false, disabler: true)
test(
	'Validate schema file',
	compile_schemas,
	args: ['--strict', '--dry-run', meson.current_source_dir()],
)

service_conf = configuration_data()
service_conf.set('bindir', get_option('prefix') / get_option('bindir'))
configure_file(
	input: 'com.github.cgueret.Scriptorium.service.in',
	output: 'com.github.cgueret.Scriptorium.service',
	configuration: service_conf,
	install_dir: get_option('datadir') / 'dbus-1' / 'services',
)

blueprints = custom_target(
	'blueprints',
	input: files(
		'gtk/help-overlay.blp',
		'ui/editor.blp',
		'ui/editor_writing.blp',
		'ui/editor_plotting.blp',
		'ui/editor_formatting.blp',
		'ui/library.blp',
		'ui/manuscript.blp',
		'ui/window.blp',
		'ui/scene.blp',
	),
	output: '.',
	command: [
		find_program('blueprint-compiler'),
		'batch-compile',
		'@OUTPUT@',
		'@CURRENT_SOURCE_DIR@',
		'@INPUT@',
	],
)

gnome.compile_resources(
	'scriptorium',
	'scriptorium.gresource.xml',
	gresource_bundle: true,
	install: true,
	install_dir: pkgdatadir,
	dependencies: blueprints,
)

subdir('icons')
