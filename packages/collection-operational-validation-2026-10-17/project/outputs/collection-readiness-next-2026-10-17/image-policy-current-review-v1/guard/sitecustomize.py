import socket

def deny(*a,**k):raise AssertionError('Review regression attempted network; forbidden')
socket.socket.connect=deny
socket.create_connection=deny
