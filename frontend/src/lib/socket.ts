import { io } from "socket.io-client"
const URL = "http://localhost:8000"
export const socket = io(URL, {
    autoConnect: false,
    transports: ["websocket"],
})
export const connectSocket = () => {
    if (!socket.connected) {
        socket.connect()
    }
}
export const disconnectSocket = () => {
    if (socket.connected) {
        socket.disconnect()
    }
}