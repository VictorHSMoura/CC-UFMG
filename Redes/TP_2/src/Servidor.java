import java.io.DataInputStream;
import java.io.DataOutputStream;
import java.io.IOException;
import java.net.*;
import java.nio.ByteBuffer;
import java.nio.charset.StandardCharsets;
import java.util.Arrays;

public class Servidor {
    public final static int SERVICE_PORT=51551;

    public static void main(String[] args) {
        try {
            ServerSocket server = new ServerSocket(SERVICE_PORT);
            Socket clientConn = server.accept();
            DataInputStream serverInput = new DataInputStream(clientConn.getInputStream());
            DataOutputStream serverOutput = new DataOutputStream(clientConn.getOutputStream());

            byte[] receivedData = new byte[1024];
            byte[] header;

            byte[] messageID;
            int receivedMessageID = 0;
            int sentMessageID;
            int messageSize = 0;

            long fileSize;
            String fileName;

            while (receivedMessageID != 3) {
                // receiving client messages
                messageSize = serverInput.read(receivedData, 0, receivedData.length);
                System.out.println("Message size: " + messageSize);

                receivedMessageID = (int) ByteBuffer.wrap(Arrays.copyOfRange(receivedData, 0, 2)).getShort();

                switch (receivedMessageID) {
                    case 1: // hello message
                        int port = 50001; // need to change this
                        byte[] portInBytes = ByteBuffer.allocate(4).putInt(port).array();

                        sentMessageID = 2;
                        messageID = ByteBuffer.allocate(2).putShort((short) sentMessageID).array();

                        header = new byte[messageID.length + portInBytes.length];
                        System.arraycopy(messageID, 0, header, 0, messageID.length);
                        System.arraycopy(portInBytes, 0, header, messageID.length, portInBytes.length);
                        serverOutput.write(header);
                        break;
                    case 3:
                        byte[] fileNameInBytes = Arrays.copyOfRange(receivedData, 2, 17);
                        fileName = new String(fileNameInBytes, StandardCharsets.UTF_8);
                        fileSize = (long) ByteBuffer.wrap(Arrays.copyOfRange(receivedData, 17, messageSize)).getLong();
                        System.out.println(receivedMessageID + ", " + fileName + ", " + fileSize);

                        // todo: alocar estruturas necessárias para o arquivo
                        // enviando mensagem ok
                        sentMessageID = 4;
                        messageID = ByteBuffer.allocate(2).putShort((short) sentMessageID).array();
                        header = messageID;
                        serverOutput.write(header);
                        break;
                        // todo: fazer case para recebimento de dados
                }
            }
            clientConn.close();

        } catch (IOException e) {
            e.printStackTrace();
        }
    }

//    UDP Part
//    public static void main(String[] args) throws IOException {
//        try {
//            DatagramSocket serverSocket = new DatagramSocket(SERVICE_PORT);
//
//            byte[] receivingDataBuffer = new byte[1024];
//            byte[] sendingDataBuffer = new byte[1024];
//
//            DatagramPacket inputPacket = new DatagramPacket(receivingDataBuffer, receivingDataBuffer.length);
//            System.out.println("Waiting for a client to connect...");
//
//            serverSocket.receive(inputPacket);
//
//            String receivedData = new String(inputPacket.getData());
//            System.out.println("Sent from the client: " + receivedData);
//
//            sendingDataBuffer = receivedData.toUpperCase().getBytes();
//
//            InetAddress senderAddress = inputPacket.getAddress();
//            int senderPort = inputPacket.getPort();
//
//            DatagramPacket outputPacket = new DatagramPacket(
//                    sendingDataBuffer, sendingDataBuffer.length,
//                    senderAddress, senderPort
//            );
//
//            serverSocket.send(outputPacket);
//            serverSocket.close();
//        } catch (SocketException e) {
//            e.printStackTrace();
//        }
//    }
}
