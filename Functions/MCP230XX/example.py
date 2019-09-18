from MCP230XX import MCP230XX
import time

i2cAddress = 0x20

MCP = MCP230XX('MCP23017', i2cAddress, '16bit')
MCP.set_mode(0, 'output') 
while True:
	MCP.output(0,1)
	time.sleep(1)
	MCP.output(0,0)
	time.sleep(1)
