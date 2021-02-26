import java.io.*;
import java.net.*;
import java.nio.ByteBuffer;
import java.nio.charset.StandardCharsets;
import java.util.Arrays;
import java.util.HashMap;

public class Servidor {
    public static void main(String[] args) {
        if (args.length != 1) {
            System.err.println("Incorrect number of arguments.");
            System.err.println("usage: java Servidor <server port> ");
            System.err.println("example: java Servidor 51551");
            return;
        }
        int tcpPort;
        try {
            tcpPort = Integer.parseInt(args[0]);
        } catch (NumberFormatException e) {
            System.err.println("The port number needs to be a integer.");
            return;
        }

        ServerSocket server;
        try {
            server = new ServerSocket(tcpPort);
        } catch (IOException e) {
            e.printStackTrace();
            return;
        }
        while (true) {
            try {
                Socket clientConn = server.accept();
                System.out.println("New client connected: " + clientConn);

                DataInputStream serverInput = new DataInputStream(clientConn.getInputStream());
                DataOutputStream serverOutput = new DataOutputStream(clientConn.getOutputStream());

                Thread clientThread = new ClientThread(clientConn, serverInput, serverOutput);
                clientThread.start();
            } catch(Exception e){
                e.printStackTrace();
            }
        }
    }
}

class ClientThread extends Thread {
    final Socket clientConn;
    final DataInputStream serverInput;
    final DataOutputStream serverOutput;

    public ClientThread(Socket clientConn, DataInputStream serverInput, DataOutputStream serverOutput) {
        this.clientConn = clientConn;
        this.serverInput = serverInput;
        this.serverOutput = serverOutput;
    }

    public DatagramSocket allocatePort() throws IOException{
        DatagramSocket clientSocket = new DatagramSocket();
        int clientPort = clientSocket.getLocalPort();
        byte[] portInBytes = ByteBuffer.allocate(4).putInt(clientPort).array();

        System.out.println("Port allocated: " + clientPort);
        int sentMessageID = 2;
        byte[] messageID = ByteBuffer.allocate(2).putShort((short) sentMessageID).array();

        byte[] header = new byte[messageID.length + portInBytes.length];
        System.arraycopy(messageID, 0, header, 0, messageID.length);
        System.arraycopy(portInBytes, 0, header, messageID.length, portInBytes.length);
        serverOutput.write(header);

        return clientSocket;
    }

    public Tuple2<String, Long> getFileInfo(byte[] receivedData, int messageSize) throws IOException {
        byte[] fileNameInBytes = Arrays.copyOfRange(receivedData, 2, 17);
        String fileName = new String(fileNameInBytes, StandardCharsets.UTF_8);
        long fileSize = ByteBuffer.wrap(Arrays.copyOfRange(receivedData, 17, messageSize)).getLong();
        System.out.println("File info - Name: " + fileName + " - Size (in bytes): " + fileSize);

        System.out.println("Allocating memory for the file");

        // sending ok message
        int sentMessageID = 4;
        byte[] header = ByteBuffer.allocate(2).putShort((short) sentMessageID).array();
        System.out.println("Ready to receive file upload");
        serverOutput.write(header);

        return new Tuple2<>(fileName, fileSize);
    }

    public static void sendAck(int lastSequenceNumber, DataOutputStream serverOutput) throws IOException {
        byte[] ackPacket = new byte[6];

        byte[] messageID = ByteBuffer.allocate(2).putShort((short) 7).array();
        byte[] sequenceNumber = ByteBuffer.allocate(4).putInt(lastSequenceNumber).array();

        System.arraycopy(messageID, 0, ackPacket, 0, messageID.length);
        System.arraycopy(sequenceNumber, 0, ackPacket, messageID.length, sequenceNumber.length);

        serverOutput.write(ackPacket);
        System.out.println("Sent ack: Sequence Number = " + lastSequenceNumber);
    }

    public void receiveFile(String fileName, long fileSize, DatagramSocket clientSocket) throws IOException {
        String destinyFile = (fileName.substring(0, fileName.indexOf(".")) + "_recebido"
                + fileName.substring(fileName.indexOf("."))).trim();

        File file = new File(destinyFile);
        FileOutputStream fileOutput = new FileOutputStream(file);

        boolean lastMessageFlag = false;
        int sequenceNumber;
        int lastSequenceNumber = -1;
        int payloadSize = 1000;
        int windowSize = 64;
        int numberOfPackets = (int) (fileSize/payloadSize);

        if (fileSize % payloadSize != 0)
            numberOfPackets++;

        HashMap<Integer, byte[]> packetsReceived = new HashMap<>();

        while (!lastMessageFlag) {
            byte[] header = new byte[1024];
            byte[] fileByteArray;
            DatagramPacket receivedPacket = new DatagramPacket(header, header.length);
            clientSocket.setSoTimeout(0);
            clientSocket.receive(receivedPacket);

            header = receivedPacket.getData();

            sequenceNumber = ByteBuffer.wrap(Arrays.copyOfRange(header, 2, 6)).getInt();
            payloadSize = ByteBuffer.wrap(Arrays.copyOfRange(header, 6, 8)).getShort();
            fileByteArray = Arrays.copyOfRange(header, 8, 8 + payloadSize);


            if (sequenceNumber == (lastSequenceNumber + 1)) {
                lastSequenceNumber = sequenceNumber;

                fileOutput.write(fileByteArray);
                System.out.println("Received: Sequence number = " + sequenceNumber + " - Size: " + payloadSize);

                sendAck(lastSequenceNumber, serverOutput);

                int lastUntilNow = lastSequenceNumber;
                for(int i = lastUntilNow + 1; i < lastUntilNow + windowSize && i < numberOfPackets -1; i++) {
                    if(packetsReceived.get(i) == null) {
                        break;
                    }
                    fileOutput.write(packetsReceived.get(i));
                    sendAck(i, serverOutput);
                    packetsReceived.remove(i);
                    lastSequenceNumber = i;
                }
                if (sequenceNumber == numberOfPackets - 1) {
                    byte[] endMessage = new byte[2];

                    byte[] messageID = ByteBuffer.allocate(2).putShort((short) 5).array();
                    System.arraycopy(messageID, 0, endMessage, 0, messageID.length);

                    System.out.println("File received.");
                    System.out.println("Sending END message.");
                    lastMessageFlag = true;

                    serverOutput.write(endMessage);
                    fileOutput.close();
                }
            } else {
                if (sequenceNumber < (lastSequenceNumber + 1)) {
                    // Send acknowledgement for received packet
                    sendAck(sequenceNumber, serverOutput);
                } else {
                    // Resend acknowledgement for last packet received
                    sendAck(lastSequenceNumber, serverOutput);

                    packetsReceived.put(sequenceNumber, fileByteArray);
                }
            }
        }
    }

    @Override
    public void run() {
        byte[] receivedData = new byte[32];

        int receivedMessageID = 0;
        int messageSize;

        long fileSize = 3;
        String fileName = "default-file.txt";

        DatagramSocket clientSocket = null;
        try {
            while (receivedMessageID != 3) {
                // receiving client messages
                messageSize = serverInput.read(receivedData, 0, receivedData.length);

                receivedMessageID = ByteBuffer.wrap(Arrays.copyOfRange(receivedData, 0, 2)).getShort();

                switch (receivedMessageID) {
                    case 1: // hello message
                        System.out.println("Hello message received. Allocating client port");

                        clientSocket = allocatePort();
                        break;
                    case 3:
                        Tuple2<String, Long> fileData = getFileInfo(receivedData, messageSize);
                        fileName = fileData.getFirst();
                        fileSize = fileData.getSecond();
                        break;
                }
            }

            receiveFile(fileName, fileSize, clientSocket);

            if (clientSocket != null) clientSocket.close();
            System.out.println("Closing connection " + clientConn);
            clientConn.close();
            System.out.println("Connection closed");

        } catch (IOException e) {
            e.printStackTrace();
        }
    }
}