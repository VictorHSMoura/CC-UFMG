import java.io.*;
import java.net.*;
import java.nio.ByteBuffer;
import java.nio.charset.StandardCharsets;
import java.util.Arrays;

public class Cliente {
    public final static int SERVICE_PORT = 51551;

    public static void main(String[] args) {
        if (args.length != 3) {
            System.err.println("Quantidade de argumentos incorreta");
            return;
        }
        String serverIP = args[0];
        String fileName = args[2];
        int port;

        try {
            port = Integer.parseInt(args[1]);
        } catch (NumberFormatException e) {
            System.err.println("A porta de conexão deve conter um valor inteiro.");
            return;
        }

        try {
            InetAddress ip = InetAddress.getByName(serverIP);
            Socket clientSocket = new Socket(ip, port);
            DataInputStream is = new DataInputStream(clientSocket.getInputStream());
            DataOutputStream out = new DataOutputStream(clientSocket.getOutputStream());
            byte[] messageID;
            byte[] header;
            byte[] receivedData = new byte[1024];
            int receivedMessageID = 0;
            int sentMessageID;
            int messageSize = 0;
            int UDPPort;

            header = ByteBuffer.allocate(2).putShort((short) 1).array();

            while (receivedMessageID != 4) {
                out.write(header);

                messageSize = is.read(receivedData, 0, receivedData.length);
                receivedMessageID = (int) ByteBuffer.wrap(Arrays.copyOfRange(receivedData, 0, 2)).getShort();
                System.out.println("Message size: " + messageSize);

                switch (receivedMessageID) {
                    case 2:
                        UDPPort = ByteBuffer.wrap(Arrays.copyOfRange(receivedData, 2, 6)).getInt();
                        System.out.println("message: " + receivedMessageID + ", " + UDPPort + " - tamanho: " + messageSize);

                        sentMessageID = 3;
                        messageID = ByteBuffer.allocate(2).putShort((short) sentMessageID).array();
                        byte[] filenameInBytes = new byte[15];
                        System.arraycopy(fileName.getBytes(), 0, filenameInBytes, 0, fileName.getBytes().length);
                        byte[] fileSize = ByteBuffer.allocate(8).putLong((long) 1e10).array();


                        header = new byte[messageID.length + filenameInBytes.length + fileSize.length];

                        System.arraycopy(messageID, 0, header, 0, messageID.length);
                        System.arraycopy(filenameInBytes, 0, header, messageID.length, filenameInBytes.length);
                        System.arraycopy(fileSize, 0, header,
                                messageID.length + filenameInBytes.length, fileSize.length);
                        break;
                    case 4:
                        System.out.println("message: " + receivedMessageID);
                        // todo: enviar o arquivo via UDP, utlizando a porta alocada
                        break;
                }
            }
            clientSocket.close();
        } catch (IOException e) {
            e.printStackTrace();
        }
    }

//    UDP PART
//    public static void main(String[] args) {
//        try{
//            DatagramSocket clientSocket = new DatagramSocket();
//
//            InetAddress IPAddress = InetAddress.getByName("localhost");
//
//            byte[] sendingDataBuffer = new byte[1024];
//            byte[] receivingDataBuffer = new byte[1024];
//
//            String sentence = "Hello from UDP client";
//            sendingDataBuffer = sentence.getBytes();
//
//            DatagramPacket sendingPacket = new DatagramPacket(sendingDataBuffer, sendingDataBuffer.length, IPAddress, SERVICE_PORT);
//
//            clientSocket.send(sendingPacket);
//
//            DatagramPacket receivingPacket = new DatagramPacket(receivingDataBuffer, receivingDataBuffer.length);
//            clientSocket.receive(receivingPacket);
//
//            String receivedData = new String(receivingPacket.getData());
//            System.out.println("Sent from the server: " + receivedData);
//
//            clientSocket.close();
//        } catch (SocketException | UnknownHostException e) {
//            e.printStackTrace();
//        } catch (IOException e) {
//            e.printStackTrace();
//        }
//    }
}
