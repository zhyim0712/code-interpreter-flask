FROM g-zwgc3422-docker.pkg.coding.net/docker/image/python:3.10

# 设置工作目录
WORKDIR /app

# 复制 requirements.txt 文件并安装依赖
COPY requirements.txt ./
RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple/
RUN pip install -r requirements.txt

# 复制项目文件
COPY src /app/src
COPY app.py /app/app.py
COPY start.sh /app/start.sh

# 创建 matplotlib 配置目录
RUN mkdir -p /.config/matplotlib
RUN chmod -R 777 /.config/matplotlib

# 复制 matplotlibrc 文件
COPY matplotlibrc /.config/matplotlib/matplotlibrc

# 复制 SimHei 字体文件
COPY SimHei.ttf /usr/local/lib/python3.10/site-packages/matplotlib/mpl-data/fonts/ttf/

# 更新 matplotlib 字体缓存
RUN python -m matplotlib.font_manager --no-cache-dir

# 开放端口
EXPOSE 8000

# 启动命令
CMD ["bash", "start.sh"]