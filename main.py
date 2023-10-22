# -*- coding: utf-8 -*-
import sys
import os
import sqlite3  # 导入SQLite库
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QPushButton, QFileDialog, QSlider, QWidget, QLabel, QMessageBox
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtCore import Qt, QUrl, QSettings, QTimer
from PyQt5.QtGui import QKeyEvent

class MusicPlayer(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("UDisk Music Player")
        self.setGeometry(100, 100, 800, 600)

        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)

        self.layout = QVBoxLayout()
        self.central_widget.setLayout(self.layout)

        self.media_player = QMediaPlayer(self)
        self.media_player.setVolume(50)

        self.play_button = QPushButton("Play", self)
        self.play_button.clicked.connect(self.play_music)
        self.layout.addWidget(self.play_button)

        self.stop_button = QPushButton("Stop", self)
        self.stop_button.clicked.connect(self.stop_music)
        self.layout.addWidget(self.stop_button)

        self.open_button = QPushButton("Open Folder", self)
        self.open_button.clicked.connect(self.open_folder)
        self.layout.addWidget(self.open_button)

        self.delete_button = QPushButton("Delete Song", self)
        self.delete_button.clicked.connect(self.delete_current_song)
        self.layout.addWidget(self.delete_button)

        self.next_button = QPushButton("Next Song", self)
        self.next_button.clicked.connect(self.play_next_song)
        self.layout.addWidget(self.next_button)

        self.volume_slider = QSlider(Qt.Horizontal, self)
        self.volume_slider.setValue(50)
        self.volume_slider.valueChanged.connect(self.set_volume)
        self.layout.addWidget(self.volume_slider)

        self.song_label = QLabel("", self)
        self.layout.addWidget(self.song_label)

        self.song_path_label = QLabel("", self)
        self.layout.addWidget(self.song_path_label)

        self.total_songs_label = QLabel("", self)
        self.layout.addWidget(self.total_songs_label)

        self.progress_slider = QSlider(Qt.Horizontal, self)
        self.progress_slider.setValue(50)
        self.progress_slider.sliderReleased.connect(self.set_progress)
        self.progress_slider.sliderPressed.connect(self.set_progress)
        self.progress_slider.sliderMoved.connect(self.set_progress)
        self.layout.addWidget(self.progress_slider)

        self.music_directory = None
        self.playlist = []
        self.current_song_index = 0

        self.settings = QSettings("YourCompany", "MusicPlayer")
        self.load_last_folder()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_progress_slider)
        self.timer.start(1000)

        self.db_connection = sqlite3.connect(self.music_directory + "/music_player.db")  # 连接到SQLite数据库
        self.create_table_if_not_exists()  # 如果表不存在则创建

        self.scan_music_files(self.music_directory)

    def play_music(self):
        if self.music_directory:
            if self.playlist:
                song = self.playlist[self.current_song_index]
                media_content = QMediaContent(QUrl.fromLocalFile(song))
                self.media_player.setMedia(media_content)
                self.song_label.setText("Now Playing: " + os.path.basename(song))
                self.song_path_label.setText(f"Path: {song}")
                self.media_player.setPosition(60*1000)
                self.media_player.play()
                self.update_current_song_label()

    def stop_music(self):
        self.media_player.stop()

    def open_folder(self):
        folder_dialog = QFileDialog.getExistingDirectory(self, "Open Folder", self.music_directory)
        if folder_dialog:
            self.music_directory = folder_dialog
            self.scan_music_files(self.music_directory)
            self.save_last_folder()

    def set_volume(self):
        volume = self.volume_slider.value()
        self.media_player.setVolume(volume)

    def scan_music_files(self, directory):
        self.playlist.clear()
        self.current_song_index = 0

        for root, _, files in os.walk(directory):
            for file in files:
                if file.lower().endswith(('.mp3', '.wav', '.flac')):
                    song = os.path.join(root, file)
                    if not self.is_song_read(song):  # 检查歌曲是否已读
                        self.playlist.append(song)

        total_songs = len(self.playlist)
        self.total_songs_label.setText(f"Total Songs: {total_songs}")
        self.update_current_song_label()

    def update_current_song_label(self):
        self.song_label.setText(f"Now Playing ({self.current_song_index + 1}/{len(self.playlist)}): {os.path.basename(self.playlist[self.current_song_index])}")
        if self.current_song_index >= 0 and self.current_song_index < len(self.playlist):
            self.song_path_label.setText(f"Path: {self.playlist[self.current_song_index]}")

    def load_last_folder(self):
        self.music_directory = self.settings.value("LastFolder")

    def save_last_folder(self):
        if self.music_directory:
            self.settings.setValue("LastFolder", self.music_directory)

    def delete_current_song(self):
        if self.playlist and self.current_song_index >= 0 and self.current_song_index < len(self.playlist):
            song_to_delete = self.playlist.pop(self.current_song_index)
            self.update_current_song_label()

            try:
                os.remove(song_to_delete)
                # self.mark_song_as_read(song_to_delete)  # 标记歌曲为已读
                if self.playlist:
                    self.play_music()
                else:
                    self.song_path_label.setText("Path: ")
            except OSError as e:
                QMessageBox.critical(self, "Error", f"Error deleting the song: {str(e)}")

    def play_next_song(self):
        if self.playlist:
            song = self.playlist[self.current_song_index]
            self.mark_song_as_read(song) 
            self.current_song_index = (self.current_song_index + 1) % len(self.playlist)
            self.play_music()


    def set_progress(self):
        progress = self.progress_slider.value()
        duration = self.media_player.duration()
        print(duration)
        self.media_player.setPosition(int(progress / 100 * duration))

    def update_progress_slider(self):
        if self.media_player.duration() > 0:
            position = self.media_player.position()
            duration = self.media_player.duration()
            self.progress_slider.setValue(int(position / duration * 100))

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Right:  # 按下右箭头键
            self.move_forward_10_seconds()
        elif event.key() == Qt.Key_Left:  # 按下左箭头键
            self.move_backward_10_seconds()
        elif event.key() == Qt.Key_Delete:  # 按下删除键
            self.delete_current_song()

    def move_forward_10_seconds(self):
        # 将当前播放位置向后移动10秒
        if self.media_player.duration() > 0:
            position = self.media_player.position()
            duration = self.media_player.duration()
            new_position = position + 10000  # 10秒等于10000毫秒
            if new_position > duration:
                new_position = duration
            self.media_player.setPosition(new_position)

    def move_backward_10_seconds(self):
        # 将当前播放位置向前移动10秒
        if self.media_player.duration() > 0:
            position = self.media_player.position()
            new_position = position - 10000  # 10秒等于10000毫秒
            if new_position < 0:
                new_position = 0
            self.media_player.setPosition(new_position)
    def create_table_if_not_exists(self):
        cursor = self.db_connection.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS songs 
                          (id INTEGER PRIMARY KEY AUTOINCREMENT,
                           path TEXT NOT NULL,
                           read INTEGER DEFAULT 0)''')
        self.db_connection.commit()

    def mark_song_as_read(self, song_path):
        cursor = self.db_connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM songs WHERE path = ?", (song_path,))
        result = cursor.fetchone()

        if result is not None and result[0] > 0:
            # QMessageBox.warning(self, "Warning", "Song is already marked as read.")
            pass
        else:
            cursor.execute("INSERT INTO songs (path, read) VALUES (?, 1)", (song_path,))
            self.db_connection.commit()
            # QMessageBox.information(self, "Information", "Song was marked as read and added to the database.")

    def is_song_read(self, song_path):
        cursor = self.db_connection.cursor()
        cursor.execute("SELECT read FROM songs WHERE path = ?", (song_path,))
        result = cursor.fetchone()
        return result is not None and result[0] == 1

    def closeEvent(self, event):
        self.db_connection.close()  # 关闭数据库连接

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            # 判断鼠标点击的位置是否在滑块上
            slider_rect = self.progress_slider.geometry()
            if slider_rect.contains(event.pos()):
                event.ignore()  # 如果在滑块上，忽略点击事件
            else:
                # 在非滑块区域点击时，获取点击位置并设置新的播放位置
                click_pos = event.pos().x()
                slider_width = slider_rect.width()
                position = int(click_pos / slider_width * self.media_player.duration())
                self.media_player.setPosition(position)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    player = MusicPlayer()
    player.show()

    try:
        sys.exit(app.exec_())
    except KeyboardInterrupt:
        sys.exit()
