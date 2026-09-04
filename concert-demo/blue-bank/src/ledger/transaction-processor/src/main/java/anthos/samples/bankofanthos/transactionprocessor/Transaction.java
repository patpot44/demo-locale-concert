package anthos.samples.bankofanthos.transactionprocessor;

import java.util.Date;
import jakarta.persistence.*;
import com.fasterxml.jackson.annotation.JsonProperty;
import com.fasterxml.jackson.annotation.JsonIgnoreProperties;

@Entity
@Table(name = "TRANSACTIONS")
@JsonIgnoreProperties(ignoreUnknown = true)
public class Transaction {
    @Id
    @Column(name = "TRANSACTION_ID")
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private long transactionId;

    @Column(name = "FROM_ACCT")
    @JsonProperty("fromAccountNum")
    private String fromAccountNum;

    @Column(name = "FROM_ROUTE")
    @JsonProperty("fromRoutingNum")
    private String fromRoutingNum;

    @Column(name = "TO_ACCT")
    @JsonProperty("toAccountNum")
    private String toAccountNum;

    @Column(name = "TO_ROUTE")
    @JsonProperty("toRoutingNum")
    private String toRoutingNum;

    @Column(name = "AMOUNT")
    @JsonProperty("amount")
    private Integer amount;

    @Column(name = "TIMESTAMP")
    @JsonProperty("timestamp")
    private Date timestamp;

    @Transient
    @JsonProperty("uuid")
    private String requestUuid;

    // Getters
    public long getTransactionId() { return transactionId; }
    public String getFromAccountNum() { return fromAccountNum; }
    public String getFromRoutingNum() { return fromRoutingNum; }
    public String getToAccountNum() { return toAccountNum; }
    public String getToRoutingNum() { return toRoutingNum; }
    public Integer getAmount() { return amount; }
    public Date getTimestamp() { return timestamp; }

    // Setters needed for deserialization
    public void setTimestamp(Date timestamp) { this.timestamp = timestamp; }

    @Override
    public String toString() {
        return String.format("%s->$%.2f->%s", fromAccountNum, amount / 100.0, toAccountNum);
    }
}
