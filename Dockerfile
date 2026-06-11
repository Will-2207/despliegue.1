FROM php:8.2-apache

# Habilitar el módulo de reescritura
RUN a2enmod rewrite

# Instalar dependencias para base de datos
RUN apt-get update && apt-get install -y libpq-dev \
    && docker-php-ext-install pdo pdo_pgsql

# Configurar Apache: mover la raíz a la carpeta /src
RUN sed -i 's|/var/www/html|/var/www/html/src|g' /etc/apache2/sites-available/000-default.conf

# Copiar TODO el código a la carpeta de Apache
COPY . /var/www/html/

# Asegurar permisos correctos
RUN chown -R www-data:www-data /var/www/html

# EXPOSE 80 porque Apache trabaja en 80 por defecto dentro del contenedor
EXPOSE 80
