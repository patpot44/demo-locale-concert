package anthos.samples.bankofanthos.transactionprocessor;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.kafka.annotation.KafkaListener;
import org.springframework.stereotype.Service;

@Service
public class TransactionConsumer {

    private static final Logger LOGGER = LoggerFactory.getLogger(TransactionConsumer.class);

    private final TransactionRepository transactionRepository;

    public TransactionConsumer(TransactionRepository transactionRepository) {
        this.transactionRepository = transactionRepository;
    }

    @KafkaListener(topics = "transactions", groupId = "transaction-processor")
    public void consume(Transaction transaction) {
        try {
            if (transaction.getTimestamp() == null) {
                transaction.setTimestamp(new java.util.Date());
            }
            transactionRepository.save(transaction);
            LOGGER.info("Saved transaction: {}", transaction);
        } catch (Exception e) {
            LOGGER.error("Failed to save transaction: {}", transaction, e);
            throw e; // Let Kafka retry
        }
    }
}
