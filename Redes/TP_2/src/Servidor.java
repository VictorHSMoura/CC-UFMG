import java.io.*;
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
            int clientPort = 54321; // need to change this

            long fileSize = 3;
            String fileName = "default-file.txt";

            while (receivedMessageID != 3) {
                // receiving client messages
                messageSize = serverInput.read(receivedData, 0, receivedData.length);

                receivedMessageID = (int) ByteBuffer.wrap(Arrays.copyOfRange(receivedData, 0, 2)).getShort();

                switch (receivedMessageID) {
                    case 1: // hello message
                         System.out.println("Hello message received. Allocating client port");

                        byte[] portInBytes = ByteBuffer.allocate(4).putInt(clientPort).array();

                        System.out.println("Port allocated: " + clientPort);
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
                        fileSize = ByteBuffer.wrap(Arrays.copyOfRange(receivedData, 17, messageSize)).getLong();
                        System.out.println("File info - Name: " + fileName + " - Size (in bytes): " + fileSize);

                        System.out.println("Allocating memory for the file");

                        // sending ok message
                        sentMessageID = 4;
                        messageID = ByteBuffer.allocate(2).putShort((short) sentMessageID).array();
                        header = messageID;
                        System.out.println("Ready to receive file upload");
                        serverOutput.write(header);
                        break;
                }
            }

            DatagramSocket clientSocket = new DatagramSocket(clientPort);
            File file = new File("arquivo-recebido.txt");
            file.createNewFile();
            FileOutputStream fileOutput = new FileOutputStream(file);

            boolean lastMessageFlag = false;
            int sequenceNumber = 0;
            int lastSequenceNumber = -1;
            int payloadSize = 0;
            int packetSize = 1000;
            int numberOfPackets = (int) (fileSize/packetSize);

            if (fileSize % packetSize != 0)
                numberOfPackets++;

            while (!lastMessageFlag) {
                byte[] message = new byte[1024];
                byte[] fileByteArray = new byte[packetSize];
                DatagramPacket receivedPacket = new DatagramPacket(message, message.length);
                clientSocket.setSoTimeout(0);
                clientSocket.receive(receivedPacket);

                message = receivedPacket.getData();
                receivedMessageID = (int) ByteBuffer.wrap(Arrays.copyOfRange(message, 0, 2)).getShort();
                sequenceNumber = ByteBuffer.wrap(Arrays.copyOfRange(message, 2, 6)).getInt();
                packetSize = ByteBuffer.wrap(Arrays.copyOfRange(message, 6, 8)).getShort();


                if (sequenceNumber == numberOfPackets - 1) {
                    lastMessageFlag = true;
                } else {
                    lastMessageFlag = false;
                }
                if (sequenceNumber == (lastSequenceNumber + 1)) {
                    lastSequenceNumber = sequenceNumber;

                    fileByteArray = Arrays.copyOfRange(message, 8, 8 + packetSize);

                    fileOutput.write(fileByteArray);
                    System.out.println("Received: Sequence number = " + sequenceNumber);
                    if (lastMessageFlag) {
                        fileOutput.close();
                    }
                }
            }

            clientSocket.close();
            System.out.println("File received.");
            System.out.println("Client " + clientConn + " sends exit...");
            System.out.println("Closing connection.");
            clientConn.close();
            System.out.println("Connection closed");

        } catch (IOException e) {
            e.printStackTrace();
        }
    }
}
