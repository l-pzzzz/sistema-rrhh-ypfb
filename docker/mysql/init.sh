#!/bin/sh
# Permiso para que pytest-django cree la base de pruebas (test_<base>) con el usuario de la aplicación.
mysql -uroot -p"$MYSQL_ROOT_PASSWORD" -e "GRANT ALL PRIVILEGES ON \`test_${MYSQL_DATABASE}\`.* TO '${MYSQL_USER}'@'%'; FLUSH PRIVILEGES;"
