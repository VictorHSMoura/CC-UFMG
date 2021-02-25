import java.io.*;
import java.net.*;
import java.nio.ByteBuffer;
import java.nio.charset.StandardCharsets;
import java.util.Arrays;
import java.util.Random;
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

        int firstIndex = fileName.indexOf(".");
        int lastIndex = fileName.lastIndexOf(".");
        boolean asciiChar = fileName.matches("\\A\\p{ASCII}*\\z");

        if (firstIndex != lastIndex || firstIndex == -1 || !asciiChar) {
            System.err.println("Filename not permitted");
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
            Thread.sleep(50); //Evita condição de corrida
            int sequenceNumber = 0;
            int ackNumber = -1;
            boolean lastMessageFlag = false;
            boolean lastIsAcked = false;
            boolean endOfCommunication = false;
            boolean retransmit = false;
            int lastAcked = -1;

            int windowSize = 64;
            int payloadSize = 1000;
            Vector<byte[]> sentMessageList = new Vector<>();
            Random randomNumber = new Random();

            int i = 0;
            while (i < fileByteArray.length) {
                try {
                    header = sentMessageList.get(sequenceNumber);
                    retransmit = false;
                } catch (ArrayIndexOutOfBoundsException e) {
                    int msgSize = payloadSize;
                    if ((i+payloadSize) >= fileByteArray.length) {
                        msgSize = fileByteArray.length - i;
                        lastMessageFlag = true;
                    }

                    sentMessageID = 6;
                    messageID = ByteBuffer.allocate(2).putShort((short) sentMessageID).array();

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
                i += payloadSize;

                DatagramPacket sendPacket = new DatagramPacket(header, header.length, ip, UDPPort);

                while (true) {
                    if ((sequenceNumber - windowSize) > lastAcked) {
                        boolean correctPacket = false;
                        boolean ackReceived = false;


                        while (!correctPacket) {
                            byte[] ack = new byte[6];

                            try {
                                clientSocket.setSoTimeout(10);
                                is.read(ack, 0, ack.length);
                                receivedMessageID = ByteBuffer.wrap(Arrays.copyOfRange(ack, 0, 2)).getShort();
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
//                                break;
                            } else {
                                // resetting window to retransmit
                                i = (lastAcked + 1) * payloadSize;
                                sequenceNumber = lastAcked;
                                retransmit = true;
                                break;
                            }
                        }
                    } else {
                        break;
                    }
                }

                if(!retransmit)
                    if(randomNumber.nextInt(10) != 0) {
                        // Package the message
                        udpSocket.send(sendPacket);
                        System.out.println("Sent: Sequence number = " + sequenceNumber + " - Size: " + payloadSize);
                    }


                // Check for acknowledgements
                while (true) {
                    boolean ackReceived = false;
                    byte[] ack = new byte[6];

                    try {
                        clientSocket.setSoTimeout(5);
                        int bytes = is.read(ack, 0, ack.length);
                        receivedMessageID = ByteBuffer.wrap(Arrays.copyOfRange(ack, 0, 2)).getShort();
                        ackNumber = ByteBuffer.wrap(Arrays.copyOfRange(ack, 2, 6)).getInt();
                        if(bytes <= 0 || receivedMessageID == 5) {
                            if (receivedMessageID == 5)
                                endOfCommunication = true;
                            break;
                        }
                        ackReceived = true;
                    } catch (SocketTimeoutException e) {
                        ackReceived = false;
                        break;
                    }

                    // Note any acknowledgements and move window forward
                    if (ackReceived) {
                        if (ackNumber >= (lastAcked + 1)) {
                            lastAcked = ackNumber;
                            System.out.println("Ack received for packet = " + ackNumber);
                        }
                    } else {
                        break;
                    }
                }

                sequenceNumber += 1;
            }

            if (!endOfCommunication) {
                while (!lastIsAcked) {

                    boolean correctPacket = false;
                    boolean ackReceived = false;

                    while (!correctPacket) {
                        // Check for an ack
                        byte[] ack = new byte[6];

                        try {
                            clientSocket.setSoTimeout(50);
                            is.read(ack, 0, ack.length);
                            ackNumber = ByteBuffer.wrap(Arrays.copyOfRange(ack, 2, 6)).getInt();
                            ackReceived = true;
                        } catch (SocketTimeoutException e) {
                            ackReceived = false;
                        }

                        // If its the last packet
                        if (lastAcked >= sequenceNumber - 1) {
                            lastIsAcked = true;
                            break;
                        }
                        // Break if we receive acknowledgement so that we can send next packet
                        if (ackReceived) {
                            if(ackNumber != 0)
                                System.out.println("Ack received for packet = " + ackNumber);
                            if (ackNumber >= (lastAcked + 1)) {
                                lastAcked = ackNumber;
                            }
                            correctPacket = true;
                            //                        break; // Break if there is an ack so the next packet can be sent
                        } else { // Resend the packet
                            // Resend the packet following the last acknowledged packet and all following that (cumulative acknowledgement)
                            for (int packInd = 0; packInd != (sequenceNumber - lastAcked); packInd++) {
                                byte[] retryMessage = new byte[1024];
                                int ind;
                                if(lastAcked == -1) //error on the first packet
                                    ind = packInd;
                                else
                                    ind = packInd + lastAcked;

                                retryMessage = sentMessageList.get(ind);

                                System.out.println("Resending: Sequence Number = " + (ind));
                                DatagramPacket retryPacket = new DatagramPacket(retryMessage, retryMessage.length, ip, UDPPort);
                                udpSocket.send(retryPacket);
                            }
                        }
                    }
                }
                endOfCommunication = true;
            }
            if (endOfCommunication) {
                System.out.println("END message received");

                // closing resources
                is.close();
                out.close();


                System.out.println("Closing this connection : " + clientSocket);
                clientSocket.close();
                System.out.println("Connection closed");
            }

        } catch (Exception e) {
            e.printStackTrace();
        }
    }
}