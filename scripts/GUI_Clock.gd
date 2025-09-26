extends Label

var start_time_ms: int
var game_state: GameState

func _ready():
	# 记录计时器启动时的毫秒时间
	start_time_ms = Time.get_ticks_msec()
	if has_node("/root/GameState"):
		game_state = get_node("/root/GameState")
	
	
func _process(_delta):
	# 每帧更新时间
	update_time_label()

func update_time_label():
	# 计算经过的毫秒数
	var elapsed_ms = Time.get_ticks_msec() - start_time_ms
	
	# 转换为小时、分钟、秒和毫秒
	var total_seconds = elapsed_ms / 1000
	var hours = total_seconds / 3600
	var minutes = (total_seconds % 3600) / 60
	var seconds = total_seconds % 60
	var milliseconds = elapsed_ms % 1000
	
	# 格式化时间字符串为 HH:MM:SS.mmm
	var time_string = "%02d:%02d:%02d.%03d" % [hours, minutes, seconds, milliseconds]
	
	# 设置 Label 文本
	text = time_string
	
	game_state.set_elapsed_ms(elapsed_ms)
