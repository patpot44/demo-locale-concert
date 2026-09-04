package anthos.samples.bankofanthos.balancereader;

import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.dao.DataAccessResourceFailureException;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.web.client.ResourceAccessException;
import com.google.common.cache.CacheBuilder;
import com.google.common.cache.CacheLoader;
import com.google.common.cache.LoadingCache;
import java.time.Duration;
import java.util.concurrent.TimeUnit;

@Configuration
public class BalanceCache {
    private static final Logger LOGGER = LogManager.getLogger(BalanceCache.class);

    @Autowired
    private TransactionRepository dbRepo;
    @Autowired
    private StringRedisTemplate redisTemplate;

    @Bean(name = "cache")
    public LoadingCache<String, Long> initializeCache(
        @Value("${CACHE_SIZE:1000000}") final Integer expireSize,
        @Value("${LOCAL_ROUTING_NUM}") String localRoutingNum) {
        CacheLoader<String, Long> loader = new CacheLoader<String, Long>() {
            @Override
            public Long load(String accountId)
                throws ResourceAccessException, DataAccessResourceFailureException {
                try {
                    String cached = redisTemplate.opsForValue().get("balance:" + accountId);
                    if (cached != null) {
                        LOGGER.info("Balance loaded from Redis for {}", accountId);
                        return Long.parseLong(cached);
                    }
                } catch (Exception e) {
                    LOGGER.warn("Redis read failed, falling back to DB: {}", e.getMessage());
                }
                LOGGER.info("Balance loaded from DB for {}", accountId);
                Long balance = dbRepo.findBalance(accountId, localRoutingNum);
                if (balance == null) { balance = 0L; }
                try {
                    redisTemplate.opsForValue().set("balance:" + accountId,
                        String.valueOf(balance), Duration.ofMinutes(5));
                } catch (Exception e) {
                    LOGGER.warn("Redis write failed: {}", e.getMessage());
                }
                return balance;
            }
        };
        return CacheBuilder.newBuilder()
            .recordStats()
            .maximumSize(expireSize)
            .expireAfterWrite(1, TimeUnit.MINUTES)
            .build(loader);
    }
}
