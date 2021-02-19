import java.io.*;
import java.net.*;
import java.nio.ByteBuffer;
import java.nio.charset.StandardCharsets;
import java.util.Arrays;
import java.util.Vector;

public class Cliente {
    public final static int SERVICE_PORT = 51551;

    public static void main(String[] args) {
        if (args.length != 3) {
            System.err.println("Incorrect number of arguments");
            return;
        }
        String serverIP = args[0];
        String fileName = args[2];
        int port;

        try {
            port = Integer.parseInt(args[1]);
        } catch (NumberFormatException e) {
            System.err.println("The port number needs to be a integer");
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
            int UDPPort = 54321;    // porta default

            DatagramSocket udpSocket = new DatagramSocket();
            File file = new File(fileName);
            InputStream fileInput = new FileInputStream(file);
            int fileLength = (int) file.length();
            byte[] fileByteArray = new byte[fileLength];
            fileInput.read(fileByteArray);

            header = ByteBuffer.allocate(2).putShort((short) 1).array();
            System.out.println("Sending hello message");

            while (receivedMessageID != 4) {
                out.write(header);

                int messageSize = is.read(receivedData, 0, receivedData.length);
                receivedMessageID = (int) ByteBuffer.wrap(Arrays.copyOfRange(receivedData, 0, 2)).getShort();

                switch (receivedMessageID) {
                    case 2:
                        UDPPort = ByteBuffer.wrap(Arrays.copyOfRange(receivedData, 2, 6)).getInt();
                        System.out.println("Transmission port: " + UDPPort);

                        // sending file data
                        sentMessageID = 3;
                        messageID = ByteBuffer.allocate(2).putShort((short) sentMessageID).array();
                        byte[] filenameInBytes = new byte[15];
                        System.arraycopy(fileName.getBytes(), 0, filenameInBytes, 0, fileName.getBytes().length);
                        byte[] fileSize = ByteBuffer.allocate(8).putLong(fileLength).array();
                        System.out.println("Sending file info");

                        header = new byte[messageID.length + filenameInBytes.length + fileSize.length];

                        System.arraycopy(messageID, 0, header, 0, messageID.length);
                        System.arraycopy(filenameInBytes, 0, header, messageID.length, filenameInBytes.length);
                        System.arraycopy(fileSize, 0, header,
                                messageID.length + filenameInBytes.length, fileSize.length);
                        break;
                    case 4:
                        System.out.println("Ready to send the file");
                        break;
                }
            }

            Thread.sleep(200); //Evita condição de corrida

            int sequenceNumber = 0;
            boolean lastMessageFlag = false;

            int windowSize = 128;
            int payloadSize = 1000;
            Vector<byte[]> sentMessageList = new Vector<>();

            for (int i=0; i < fileByteArray.length; i = i+payloadSize) {
                if ((i+payloadSize) >= fileByteArray.length) {
                    payloadSize = fileByteArray.length - i;
                }

                sentMessageID = 3;
                messageID = ByteBuffer.allocate(2).putShort((short) sentMessageID).array();

                byte[] sequenceNumberInBytes = ByteBuffer.allocate(4).putInt(sequenceNumber).array();
                // Create new byte array for message
                byte[] message = new byte[1024];

                byte[] payloadSizeInBytes = ByteBuffer.allocate(2).putShort((short) payloadSize).array();

                header = new byte[messageID.length + sequenceNumberInBytes.length + payloadSizeInBytes.length + payloadSize];

                System.arraycopy(messageID, 0, header, 0, messageID.length);
                System.arraycopy(sequenceNumberInBytes, 0, header, messageID.length, sequenceNumberInBytes.length);
                System.arraycopy(payloadSizeInBytes, 0, header,
                        (messageID.length + sequenceNumberInBytes.length), payloadSizeInBytes.length);
                System.arraycopy(fileByteArray, i, header,
                        (messageID.length + sequenceNumberInBytes.length + payloadSizeInBytes.length),
                        payloadSize);

                // Package the message
                DatagramPacket sendPacket = new DatagramPacket(header, header.length, ip, UDPPort);
                udpSocket.send(sendPacket);
                System.out.println("Sent: Sequence number = " + sequenceNumber);

                // Add the message to the sent message list
                sentMessageList.add(message);
                sequenceNumber += 1;
            }

            // closing resources
            is.close();
            out.close();


            System.out.println("Closing this connection : " + clientSocket);
            clientSocket.close();
            System.out.println("Connection closed");

        } catch (Exception e) {
            e.printStackTrace();
        }
    }
}