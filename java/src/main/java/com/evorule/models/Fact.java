package com.evorule.models;

import com.fasterxml.jackson.annotation.JsonProperty;
import com.fasterxml.jackson.databind.JsonNode;

public class Fact {
    @JsonProperty("id")
    private long id;

    @JsonProperty("type")
    private String type;

    @JsonProperty("cause")
    private Long cause;

    @JsonProperty("instruction")
    private JsonNode instruction;

    @JsonProperty("new_payload")
    private JsonNode newPayload;

    @JsonProperty("new_queue")
    private JsonNode newQueue;

    @JsonProperty("io_type")
    private String ioType;

    @JsonProperty("params")
    private JsonNode params;

    @JsonProperty("request_id")
    private Long requestId;

    @JsonProperty("result")
    private JsonNode result;

    @JsonProperty("error")
    private String error;

    @JsonProperty("final_snapshot")
    private JsonNode finalSnapshot;

    @JsonProperty("message")
    private String message;

    @JsonProperty("version")
    private Long version;

    public long getId() { return id; }
    public void setId(long id) { this.id = id; }

    public String getType() { return type; }
    public void setType(String type) { this.type = type; }

    public Long getCause() { return cause; }
    public void setCause(Long cause) { this.cause = cause; }

    public JsonNode getInstruction() { return instruction; }
    public void setInstruction(JsonNode instruction) { this.instruction = instruction; }

    public JsonNode getNewPayload() { return newPayload; }
    public void setNewPayload(JsonNode newPayload) { this.newPayload = newPayload; }

    public JsonNode getNewQueue() { return newQueue; }
    public void setNewQueue(JsonNode newQueue) { this.newQueue = newQueue; }

    public String getIoType() { return ioType; }
    public void setIoType(String ioType) { this.ioType = ioType; }

    public JsonNode getParams() { return params; }
    public void setParams(JsonNode params) { this.params = params; }

    public Long getRequestId() { return requestId; }
    public void setRequestId(Long requestId) { this.requestId = requestId; }

    public JsonNode getResult() { return result; }
    public void setResult(JsonNode result) { this.result = result; }

    public String getError() { return error; }
    public void setError(String error) { this.error = error; }

    public JsonNode getFinalSnapshot() { return finalSnapshot; }
    public void setFinalSnapshot(JsonNode finalSnapshot) { this.finalSnapshot = finalSnapshot; }

    public String getMessage() { return message; }
    public void setMessage(String message) { this.message = message; }

    public Long getVersion() { return version; }
    public void setVersion(Long version) { this.version = version; }
}
