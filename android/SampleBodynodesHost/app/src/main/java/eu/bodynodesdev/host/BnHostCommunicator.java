package eu.bodynodesdev.host;

import org.json.JSONArray;

public interface BnHostCommunicator {


    void start();
    void stop();
    String getMessage(String player, String bodypart, String sensortype);
    String getMessages();
    void sendAction(JSONArray action);

}
