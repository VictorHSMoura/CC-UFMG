import java.io.*;
import java.net.*;
import java.nio.ByteBuffer;
import java.util.Arrays;
import java.util.Random;
import java.util.Vector;

public class Cliente {
    public static byte[] sendFileInfo(String fileName, long fileLength) {
        // sending file data
        int sentMessageID = 3;
        byte[] messageID = ByteBuffer.allocate(2).putShort((short) sentMessageID).array();
        byte[] filenameInBytes = new byte[15];
        System.arraycopy(fileName.getBytes(), 0, filenameInBytes, 0, fileName.getBytes().length);
        byte[] fileSize = ByteBuffer.allocate(8).putLong(fileLength).array();
        System.out.println("Sending file info");

        byte[] header = new byte[messageID.length + filenameInBytes.length + fileSize.length];

        System.arraycopy(messageID, 0, header, 0, messageID.length);
        System.arraycopy(filenameInBytes, 0, header, messageID.length, filenameInBytes.length);
        System.arraycopy(fileSize, 0, header,
                messageID.length + filenameInBytes.length, fileSize.length);

        return header;
    }

    public static Tuple2<byte[], Vector<byte[]>> getHeader(int i, int sequenceNumber, int payloadSize,
                                                           byte[] fileByteArray, Vector<byte[]> sentMessageList) {
        byte[] header;
        try {
            header = sentMessageList.get(sequenceNumber);
        } catch (ArrayIndexOutOfBoundsException e) {
            int msgSize = payloadSize;
            if ((i + payloadSize) >= fileByteArray.length) {
                msgSize = fileByteArray.length - i;
            }

            int sentMessageID = 6;
            byte[] messageID = ByteBuffer.allocate(2).putShort((short) sentMessageID).array();

            byte[] sequenceNumberInBytes = ByteBuffer.allocate(4).putInt(sequenceNumber).array();

            byte[] payloadSizeInBytes = ByteBuffer.allocate(2).putShort((short) msgSize).array();

            header = new byte[messageID.length + sequenceNumberInBytes.length + payloadSizeInBytes.length + msgSize];

            System.arraycopy(messageID, 0, header, 0, messageID.length);
            System.arraycopy(sequenceNumberInBytes, 0, header, messageID.length, sequenceNumberInBytes.length);
            System.arraycopy(payloadSizeInBytes, 0, header,
                    (messageID.length + sequenceNumberInBytes.length), payloadSizeInBytes.length);
            System.arraycopy(fileByteArray, i, header,
                    (messageID.length + sequenceNumberInBytes.length + payloadSizeInBytes.length),
                    msgSize);

            // Add the message to the sent message list
            sentMessageList.add(header);
        }
        return new Tuple2<>(header, sentMessageList);
    }

    public static int sendFile(byte[] fileByteArray, InetAddress ip, int UDPPort, Socket clientSocket,
                                InputStream is, DatagramSocket udpSocket) throws Exception {
        int sequenceNumber = 0;
        int ackNumber = -1;
        boolean endOfCommunication = false;
        boolean retransmit = false;
        int lastAcked = -1;
        byte[] header = new byte[1024];
        int retransmissions = 0;

        int windowSize = 64;
        int payloadSize = 1000;
        Vector<byte[]> sentMessageList = new Vector<>();

        int numberOfPackets = (fileByteArray.length/payloadSize);

        if (fileByteArray.length % payloadSize != 0)
            numberOfPackets++;

        int i = 0;
        while (!endOfCommunication) {
            if (sequenceNumber < numberOfPackets) {
                Tuple2<byte[], Vector<byte[]>> messageInfo = getHeader(i, sequenceNumber, payloadSize, fileByteArray, sentMessageList);
                header = messageInfo.getFirst();
                sentMessageList = messageInfo.getSecond();

                retransmit = false;
                i += payloadSize;
            }

            DatagramPacket sendPacket = new DatagramPacket(header, header.length, ip, UDPPort);

            while (true) {
                if ((sequenceNumber - windowSize) > lastAcked) {
                    boolean correctPacket = false;
                    boolean ackReceived;


                    while (!correctPacket) {
                        byte[] ack = new byte[6];

                        try {
                            clientSocket.setSoTimeout(100);
                            is.read(ack, 0, ack.length);
                            ackNumber = ByteBuffer.wrap(Arrays.copyOfRange(ack, 2, 6)).getInt();
                            ackReceived = true;
                        } catch (SocketTimeoutException e) {
                            ackReceived = false;
                        }

                        if (ackReceived) {
                            if (ackNumber >= (lastAcked + 1)) {
                                lastAcked = ackNumber;
                            }
                            correctPacket = true;
                            System.out.println("Ack received for packet = " + ackNumber);
                        } else {
                            // resetting window to retransmit
                            i = (lastAcked + 1) * payloadSize;
                            sequenceNumber = lastAcked;
                            retransmit = true;
                            retransmissions++;
                            System.out.println("Retransmitting from packet " + (sequenceNumber + 1));
                            break;
                        }
                    }
                } else {
                    break;
                }
            }

            if(!retransmit && sequenceNumber < numberOfPackets) {
                // Package the message
                udpSocket.send(sendPacket);
                System.out.println("Sent: Sequence number = " + sequenceNumber);
            }

            // Check for acknowledgements
            while (true) {
                byte[] ack = new byte[6];

                try {
                    clientSocket.setSoTimeout(100);
                    int bytes = is.read(ack, 0, ack.length);
                    int receivedMessageID = ByteBuffer.wrap(Arrays.copyOfRange(ack, 0, 2)).getShort();
                    ackNumber = ByteBuffer.wrap(Arrays.copyOfRange(ack, 2, 6)).getInt();
                    if(bytes <= 0 || receivedMessageID == 5) {
                        if (receivedMessageID == 5)
                            endOfCommunication = true;
                        break;
                    }
                } catch (SocketTimeoutException e) {
                    break;
                }

                if (ackNumber >= (lastAcked + 1)) {
                    lastAcked = ackNumber;
                    System.out.println("Ack received for packet = " + ackNumber);
                }
            }

            sequenceNumber += 1;
        }
        return retransmissions;
    }

    public static void main(String[] args) {
        if (args.length != 3) {
            System.err.println("Incorrect number of arguments.");
            return;
        }
        String serverIP = args[0];
        String fileName = args[2];
        int port;

        try {
            port = Integer.parseInt(args[1]);
        } catch (NumberFormatException e) {
            System.err.println("The port number needs to be a integer.");
            return;
        }

        int firstIndex = fileName.indexOf(".");
        int lastIndex = fileName.lastIndexOf(".");
        boolean asciiChar = fileName.matches("\\A\\p{ASCII}*\\z");

        if (firstIndex != lastIndex || firstIndex == -1 || !asciiChar) {
            System.err.println("Filename not permitted.");
            return;
        }

        try {
            InetAddress ip = InetAddress.getByName(serverIP);
            Socket clientSocket = new Socket(ip, port);

            DataInputStream is = new DataInputStream(clientSocket.getInputStream());
            DataOutputStream out = new DataOutputStream(clientSocket.getOutputStream());

            byte[] header;
            byte[] receivedData = new byte[1024];

            int receivedMessageID = 0;
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

                is.read(receivedData, 0, receivedData.length);
                receivedMessageID = ByteBuffer.wrap(Arrays.copyOfRange(receivedData, 0, 2)).getShort();

                switch (receivedMessageID) {
                    case 2:
                        UDPPort = ByteBuffer.wrap(Arrays.copyOfRange(receivedData, 2, 6)).getInt();
                        System.out.println("Transmission port: " + UDPPort);

                        // sending file data
                        header = sendFileInfo(fileName,  fileLength);
                        break;
                    case 4:
                        System.out.println("Ready to send the file");
                        break;
                }
            }
            Thread.sleep(50);
            int retransmissions = sendFile(fileByteArray, ip, UDPPort, clientSocket, is, udpSocket);

            System.out.println("END message received");
            System.out.println("Number of retranmissions: " + retransmissions);

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