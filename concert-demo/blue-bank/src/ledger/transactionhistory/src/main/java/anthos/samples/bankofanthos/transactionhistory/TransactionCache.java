package anthos.samples.bankofanthos.transactionhistory;

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.DeserializationFeature;
import com.google.common.cache.CacheBuilder;
import com.google.common.cache.CacheLoader;
import com.google.common.cache.LoadingCache;
import java.time.Duration;
import java.util.ArrayDeque;
import java.util.Deque;
import java.util.concurrent.TimeUnit;
import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.dao.DataAccessResourceFailureException;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.web.client.ResourceAccessException;

@Configuration
public class TransactionCache {
    private static final Logger LOGGER = LogManager.getLogger(TransactionCache.class);

    @Autowired
    private TransactionRepository dbRepo;
    @Autowired
    private StringRedisTemplate redisTemplate;
    private final ObjectMapper objectMapper = new ObjectMapper()
        .configure(DeserializationFeature.FAIL_ON_UNKNOWN_PROPERTIES, false);

    @Bean(name = "cache")
    public LoadingCache<String, Deque<Transaction>> initializeCache(
        @Value("${CACHE_SIZE:1000000}") final Integer expireSize,
        @Value("${CACHE_MINUTES:60}") final Integer expireMinutes,
        @Value("${LOCAL_ROUTING_NUM}") String localRoutingNum,
        @Value("${HISTORY_LIMIT:100}") Integer historyLimit) {
        CacheLoader<String, Deque<Transaction>> loader =
            new CacheLoader<String, Deque<Transaction>>() {
                @Override
                public Deque<Transaction> load(String accountId)
                    throws ResourceAccessException, DataAccessResourceFailureException {
                    try {
                        String cached = redisTemplate.opsForValue().get("txn:" + accountId);
                        if (cached != null) {
                            LOGGER.info("Transactions loaded from Redis for {}", accountId);
                            return objectMapper.readValue(cached,
                                new TypeReference<ArrayDeque<Transaction>>() {});
                        }
                    } catch (Exception e) {
                        LOGGER.warn("Redis read failed, falling back to DB: {}", e.getMessage());
                    }
                    LOGGER.info("Transactions loaded from DB for {}", accountId);
                    Pageable request = PageRequest.of(0, historyLimit);
                    Deque<Transaction> transactions = dbRepo.findForAccount(
                        accountId, localRoutingNum, request);
                    try {
                        redisTemplate.opsForValue().set("txn:" + accountId,
                            objectMapper.writeValueAsString(transactions),
                            Duration.ofMinutes(expireMinutes));
                    } catch (Exception e) {
                        LOGGER.warn("Redis write failed: {}", e.getMessage());
                    }
                    return transactions;
                }
            };
        return CacheBuilder.newBuilder()
            .recordStats()
            .maximumSize(expireSize)
            .expireAfterWrite(expireMinutes, TimeUnit.MINUTES)
            .build(loader);
    }
}
