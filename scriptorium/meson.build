pkgdatadir = get_option('prefix') / get_option('datadir') / meson.project_name()
moduledir = pkgdatadir / 'scriptorium'
gnome = import('gnome')

python = import('python')

conf = configuration_data()
conf.set('PYTHON', python.find_installation('python3').full_path())
conf.set('VERSION', meson.project_version())
conf.set('localedir', get_option('prefix') / get_option('localedir'))
conf.set('pkgdatadir', pkgdatadir)

configure_file(
  input: 'scriptorium.in',
  output: 'scriptorium',
  configuration: conf,
  install: true,
  install_dir: get_option('bindir'),
  install_mode: 'r-xr-xr-x'
)

scriptorium_sources = [
  '__init__.py',
  'main.py',
  'window.py',
  'editor.py',
  'editor_writing.py',
  'editor_plotting.py',
  'editor_formatting.py',
  'scene.py',
  'library.py',
  'model.py',
  'utils.py'
]

install_data(scriptorium_sources, install_dir: moduledir)
