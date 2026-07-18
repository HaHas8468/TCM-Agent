FROM mysql:8.4

# 将初始化脚本打包进镜像，并显式赋予 MySQL 初始化用户可读权限。
# 避免 FNOS/NAS 对运行时 bind mount 的权限映射导致脚本变为 000。
COPY --chmod=644 scripts/init_mysql.sql /docker-entrypoint-initdb.d/01-init.sql
