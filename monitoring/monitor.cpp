#include <fastdds/dds/domain/DomainParticipantFactory.hpp>
#include <fastdds/dds/domain/DomainParticipant.hpp>
#include <fastdds/dds/topic/TypeSupport.hpp>
#include <fastdds/dds/publisher/qos/PublisherQos.hpp>
#include <fastdds/dds/subscriber/Subscriber.hpp>
#include <fastdds/dds/subscriber/DataReader.hpp>
#include <fastdds/dds/subscriber/qos/DataReaderQos.hpp>
#include <fastdds/dds/subscriber/SampleInfo.hpp>
#include <fastdds/dds/core/status/StatusMask.hpp>
#include <fastdds/dds/core/status/SubscriptionMatchedStatus.hpp>
#include <fastdds/dds/core/status/StatusMask.hpp>
#include <fastdds/rtps/common/Types.hpp>

#include <iostream>
#include <atomic>
#include <csignal>
#include <condition_variable>
#include <mutex>
#include <thread>
#include <sstream>
#include <mutex>
#include <vector>
#include <string>
#include <sstream>
#include <cstdlib>
#include <filesystem>
#include <unistd.h>
#include <cstring>

#include "CoreDataPubSubTypes.hpp"
#include "IntelligencePubSubTypes.hpp"
#include "MessagingPubSubTypes.hpp"

using namespace eprosima::fastdds::dds;

static std::atomic_bool g_stop{false};
static std::mutex g_io_mutex; // serialize stdout to avoid interleaved lines across readers

static std::vector<int> parse_domains_from_input(const std::string& input) {
    std::vector<int> result;
    std::stringstream ss(input);
    std::string token;
    while (std::getline(ss, token, ',')) {
        if (token.empty()) continue;
        // support ranges like "0-3"
        std::size_t dash = token.find('-');
        if (dash != std::string::npos) {
            std::string start_str = token.substr(0, dash);
            std::string end_str = token.substr(dash + 1);
            if (!start_str.empty() && !end_str.empty()) {
                int start = std::atoi(start_str.c_str());
                int end = std::atoi(end_str.c_str());
                if (end < start) std::swap(start, end);
                for (int d = start; d <= end; ++d) {
                    result.push_back(d);
                }
            }
        } else {
            result.push_back(std::atoi(token.c_str()));
        }
    }
    return result;
}

class CoreDataMonitor : public DataReaderListener {
public:
    CoreDataMonitor(int domain_id)
        : samples_(0)
        , domain_id_(domain_id) {}

    void on_data_available(DataReader* reader) override {
        CoreData::FlatCoreData sample;
        SampleInfo info;
        while (!g_stop.load() && reader->take_next_sample(&sample, &info) == RETCODE_OK) {
            if ((info.instance_state == ALIVE_INSTANCE_STATE) && info.valid_data) {
                std::string topic_name = reader->get_topicdescription() ? reader->get_topicdescription()->get_name() : std::string();
                const char* subtype = "coredata";
                if (!topic_name.empty()) {
                    if (topic_name == "CoreData2Topic") subtype = "coredata2";
                    else if (topic_name == "CoreData3Topic") subtype = "coredata3";
                    else if (topic_name == "CoreData4Topic") subtype = "coredata4";
                    else subtype = "coredata";
                }
                std::ostringstream oss;
                oss << "[domain=" << domain_id_ << "] TOPIC: aircraft " << subtype << "\n";
                oss << "Sample '" << (++samples_) << "' RECEIVED\n";
                oss << " - {"
                    << "latitude: " << sample.latitude() << ", "
                    << "longitude: " << sample.longitude() << ", "
                    << "altitude: " << sample.altitude() << ", "
                    << "time_seconds: " << sample.time_seconds() << ", "
                    << "time_nano_seconds: " << sample.time_nano_seconds() << ", "
                    << "speed_mps: " << sample.speed_mps() << ", "
                    << "orientation_degrees: " << sample.orientation_degrees()
                    << "}";
                std::lock_guard<std::mutex> lk(g_io_mutex);
                std::cout << oss.str() << std::endl;
            }
        }
    }

    void on_subscription_matched(
            DataReader* /*reader*/,
            const SubscriptionMatchedStatus& info) override {
        std::cout << "[monitor] CoreData matched change: current_count="
                  << info.current_count << " total_count=" << info.total_count << std::endl;
    }

private:
    size_t samples_;
    int domain_id_;
};

class IntelligenceMonitor : public DataReaderListener {
public:
    IntelligenceMonitor(int domain_id)
        : samples_(0)
        , domain_id_(domain_id) {}

    void on_data_available(DataReader* reader) override {
        Intelligence::FlatIntelligence sample;
        SampleInfo info;
        while (!g_stop.load() && reader->take_next_sample(&sample, &info) == RETCODE_OK) {
            if ((info.instance_state == ALIVE_INSTANCE_STATE) && info.valid_data) {
                std::ostringstream oss;
                oss << "[domain=" << domain_id_ << "] TOPIC: intelligence\n";
                oss << "Sample '" << (++samples_) << "' RECEIVED\n";
                oss << " - {"
                    << "vs_task_status: " << sample.vs_task_status() << ", "
                    << "vs_battery_percentage: " << sample.vs_battery_percentage() << ", "
                    << "vs_signal_strength_dbm: " << sample.vs_signal_strength_dbm() << ", "
                    << "vs_system_error: " << (sample.vs_system_error() ? "true" : "false") << ", "
                    << "td_target_ID: \"" << sample.td_target_ID() << "\", "
                    << "td_target_type: " << sample.td_target_type() << ", "
                    << "td_location_latitude: " << sample.td_location_latitude() << ", "
                    << "td_location_longitude: " << sample.td_location_longitude() << ", "
                    << "td_location_altitude: " << sample.td_location_altitude() << ", "
                    << "td_location_time_seconds: " << sample.td_location_time_seconds() << ", "
                    << "td_location_time_nano_seconds: " << sample.td_location_time_nano_seconds() << ", "
                    << "td_location_speed_mps: " << sample.td_location_speed_mps() << ", "
                    << "td_location_orientation_degrees: " << sample.td_location_orientation_degrees() << ", "
                    << "td_confidence_level: " << sample.td_confidence_level() << ", "
                    << "td_description: \"" << sample.td_description() << "\", "
                    << "td_raw_data_link: \"" << sample.td_raw_data_link() << "\", "
                    << "ta_command: \"" << sample.ta_command() << "\", "
                    << "ta_location_latitude: " << sample.ta_location_latitude() << ", "
                    << "ta_location_longitude: " << sample.ta_location_longitude() << ", "
                    << "ta_location_altitude: " << sample.ta_location_altitude() << ", "
                    << "ta_location_time_seconds: " << sample.ta_location_time_seconds() << ", "
                    << "ta_location_time_nano_seconds: " << sample.ta_location_time_nano_seconds() << ", "
                    << "ta_location_speed_mps: " << sample.ta_location_speed_mps() << ", "
                    << "ta_location_orientation_degrees: " << sample.ta_location_orientation_degrees()
                    << "}";
                std::lock_guard<std::mutex> lk(g_io_mutex);
                std::cout << oss.str() << std::endl;
            }
        }
    }

    void on_subscription_matched(
            DataReader* /*reader*/,
            const SubscriptionMatchedStatus& info) override {
        std::cout << "[monitor] Intelligence matched change: current_count="
                  << info.current_count << " total_count=" << info.total_count << std::endl;
    }

private:
    size_t samples_;
    int domain_id_;
};

class MessagingMonitor : public DataReaderListener {
public:
    MessagingMonitor(int domain_id)
        : samples_(0)
        , domain_id_(domain_id) {}

    void on_data_available(DataReader* reader) override {
        Messaging::FlatMessagingPacket sample;
        SampleInfo info;
        while (!g_stop.load() && reader->take_next_sample(&sample, &info) == RETCODE_OK) {
            if ((info.instance_state == ALIVE_INSTANCE_STATE) && info.valid_data) {
                std::ostringstream oss;
                oss << "[domain=" << domain_id_ << "] TOPIC: messaging\n";
                oss << "Sample '" << (++samples_) << "' RECEIVED\n";
                oss << " - {"
                    << "message_type: " << sample.message_type() << ", "
                    << "sr_header_sender_id: \"" << sample.sr_header_sender_id() << "\", "
                    << "sr_header_time_seconds: " << sample.sr_header_time_seconds() << ", "
                    << "sr_header_time_nano_seconds: " << sample.sr_header_time_nano_seconds() << ", "
                    << "sr_location_latitude: " << sample.sr_location_latitude() << ", "
                    << "sr_location_longitude: " << sample.sr_location_longitude() << ", "
                    << "sr_location_altitude: " << sample.sr_location_altitude() << ", "
                    << "sr_location_time_seconds: " << sample.sr_location_time_seconds() << ", "
                    << "sr_location_time_nano_seconds: " << sample.sr_location_time_nano_seconds() << ", "
                    << "sr_location_speed_mps: " << sample.sr_location_speed_mps() << ", "
                    << "sr_location_orientation_degrees: " << sample.sr_location_orientation_degrees() << ", "
                    << "sr_status_task_status: " << sample.sr_status_task_status() << ", "
                    << "sr_status_battery_percentage: " << sample.sr_status_battery_percentage() << ", "
                    << "sr_status_signal_strength_dbm: " << sample.sr_status_signal_strength_dbm() << ", "
                    << "sr_status_system_error: " << (sample.sr_status_system_error() ? "true" : "false") << ", "
                    << "cd_header_sender_id: \"" << sample.cd_header_sender_id() << "\", "
                    << "cd_header_time_seconds: " << sample.cd_header_time_seconds() << ", "
                    << "cd_header_time_nano_seconds: " << sample.cd_header_time_nano_seconds() << ", "
                    << "cd_detection_target_ID: \"" << sample.cd_detection_target_ID() << "\", "
                    << "cd_detection_target_type: " << sample.cd_detection_target_type() << ", "
                    << "cd_detection_loc_latitude: " << sample.cd_detection_loc_latitude() << ", "
                    << "cd_detection_loc_longitude: " << sample.cd_detection_loc_longitude() << ", "
                    << "cd_detection_loc_altitude: " << sample.cd_detection_loc_altitude() << ", "
                    << "cd_detection_loc_time_seconds: " << sample.cd_detection_loc_time_seconds() << ", "
                    << "cd_detection_loc_time_nano_seconds: " << sample.cd_detection_loc_time_nano_seconds() << ", "
                    << "cd_detection_loc_speed_mps: " << sample.cd_detection_loc_speed_mps() << ", "
                    << "cd_detection_loc_orientation_degrees: " << sample.cd_detection_loc_orientation_degrees() << ", "
                    << "cd_detection_confidence_level: " << sample.cd_detection_confidence_level() << ", "
                    << "cd_detection_description: \"" << sample.cd_detection_description() << "\", "
                    << "cd_detection_raw_data_link: \"" << sample.cd_detection_raw_data_link() << "\", "
                    << "tc_header_sender_id: \"" << sample.tc_header_sender_id() << "\", "
                    << "tc_header_time_seconds: " << sample.tc_header_time_seconds() << ", "
                    << "tc_header_time_nano_seconds: " << sample.tc_header_time_nano_seconds() << ", "
                    << "tc_receiver_id: \"" << sample.tc_receiver_id() << "\", "
                    << "tc_assignment_command: \"" << sample.tc_assignment_command() << "\", "
                    << "tc_assignment_loc_latitude: " << sample.tc_assignment_loc_latitude() << ", "
                    << "tc_assignment_loc_longitude: " << sample.tc_assignment_loc_longitude() << ", "
                    << "tc_assignment_loc_altitude: " << sample.tc_assignment_loc_altitude() << ", "
                    << "tc_assignment_loc_time_seconds: " << sample.tc_assignment_loc_time_seconds() << ", "
                    << "tc_assignment_loc_time_nano_seconds: " << sample.tc_assignment_loc_time_nano_seconds() << ", "
                    << "tc_assignment_loc_speed_mps: " << sample.tc_assignment_loc_speed_mps() << ", "
                    << "tc_assignment_loc_orientation_degrees: " << sample.tc_assignment_loc_orientation_degrees()
                    << "}";
                std::lock_guard<std::mutex> lk(g_io_mutex);
                std::cout << oss.str() << std::endl;
            }
        }
    }

    void on_subscription_matched(
            DataReader* /*reader*/,
            const SubscriptionMatchedStatus& info) override {
        std::cout << "[monitor] Messaging matched change: current_count="
                  << info.current_count << " total_count=" << info.total_count << std::endl;
    }

private:
    size_t samples_;
    int domain_id_;
};

int main(int argc, char** argv) {
    std::vector<int> domains;
    // priority: CLI arg > MONITOR_DOMAINS env > default 0-5
    if (argc > 1 && argv[1] && std::string(argv[1]).size() > 0) {
        domains = parse_domains_from_input(std::string(argv[1]));
    } else if (const char* env = std::getenv("MONITOR_DOMAINS")) {
        domains = parse_domains_from_input(std::string(env));
    }
    if (domains.empty()) {
        domains = {0, 1, 2, 3, 4, 5};
    }

    auto factory = DomainParticipantFactory::get_instance();

    struct DomainContext {
        int id;
        DomainParticipant* participant{nullptr};
        Subscriber* subscriber{nullptr};
        Topic* cd_topic{nullptr};
        Topic* cd2_topic{nullptr};
        Topic* cd3_topic{nullptr};
        Topic* cd4_topic{nullptr};
        Topic* intel_topic{nullptr};
        Topic* msg_topic{nullptr};
        DataReader* cd_reader{nullptr};
        DataReader* cd2_reader{nullptr};
        DataReader* cd3_reader{nullptr};
        DataReader* cd4_reader{nullptr};
        DataReader* intel_reader{nullptr};
        DataReader* msg_reader{nullptr};
        CoreDataMonitor* cd_listener{nullptr};
        IntelligenceMonitor* intel_listener{nullptr};
        MessagingMonitor* msg_listener{nullptr};
    };

    std::vector<DomainContext> contexts;
    contexts.reserve(domains.size());

    // Resolve DDS root directory dynamically
    auto resolve_dss_root = []() -> std::filesystem::path {
        if (const char* env_root = std::getenv("DDS_ROOT")) {
            std::filesystem::path p(env_root);
            if (std::filesystem::exists(p)) return p;
        }
        // Walk upwards from current directory to find repo root (has secure_dds and IDL)
        std::filesystem::path cur = std::filesystem::current_path();
        for (int i = 0; i < 6 && !cur.empty(); ++i) {
            if (std::filesystem::exists(cur / "secure_dds") && std::filesystem::exists(cur / "IDL")) {
                return cur;
            }
            cur = cur.parent_path();
        }
        return std::filesystem::current_path();
    };

    const std::filesystem::path dds_root = resolve_dss_root();

    // Detect hostname dynamically
    char hostname[256] = {0};
    if (gethostname(hostname, sizeof(hostname) - 1) != 0) {
        std::strcpy(hostname, "UNKNOWN_HOST");
    }
    std::string participant_dir = std::string(hostname);

    for (int domain_id : domains) {
        DomainParticipantQos pqos = PARTICIPANT_QOS_DEFAULT;

        // DDS Security Configuration - Authentication + Encryption Only
        pqos.properties().properties().emplace_back("dds.sec.auth.plugin", "builtin.PKI-DH");
        pqos.properties().properties().emplace_back("dds.sec.crypto.plugin", "builtin.AES-GCM-GMAC");

        // Certificate and Key Paths (dynamic, repo-relative or DDS_ROOT)
        const std::string uri_prefix = "file://";
        const std::filesystem::path ca_path = dds_root / "secure_dds/CA/mainca_cert.pem";
        const std::filesystem::path cert_path = dds_root / "secure_dds/participants" / participant_dir / (participant_dir + "_cert.pem");
        const std::filesystem::path key_path = dds_root / "secure_dds/participants" / participant_dir / (participant_dir + "_key.pem");

        pqos.properties().properties().emplace_back(
            "dds.sec.auth.builtin.PKI-DH.identity_ca",
            uri_prefix + ca_path.string());
        pqos.properties().properties().emplace_back(
            "dds.sec.auth.builtin.PKI-DH.identity_certificate",
            uri_prefix + cert_path.string());
        pqos.properties().properties().emplace_back(
            "dds.sec.auth.builtin.PKI-DH.private_key",
            uri_prefix + key_path.string());

        // Access Control disabled - no governance/permissions needed
        pqos.name("DDS_Monitor_participant");

        DomainContext ctx;
        ctx.id = domain_id;
        ctx.participant = factory->create_participant(domain_id, pqos);
        if (!ctx.participant) {
            std::cerr << "Failed to create DomainParticipant for domain " << domain_id << std::endl;
            continue;
        }
        std::cout << "Monitor: DomainParticipant created for domain " << domain_id << std::endl;

        ctx.subscriber = ctx.participant->create_subscriber(SUBSCRIBER_QOS_DEFAULT);
        if (!ctx.subscriber) {
            std::cerr << "Failed to create Subscriber for domain " << domain_id << std::endl;
            factory->delete_participant(ctx.participant);
            continue;
        }
        std::cout << "Monitor: Subscriber created for domain " << domain_id << std::endl;

        DataReaderQos rqos = DATAREADER_QOS_DEFAULT;
        // Payload Encryption Configuration
        rqos.properties().properties().emplace_back("rtps.payload_protection", "ENCRYPT");
        ctx.subscriber->get_default_datareader_qos(rqos);
        rqos.reliability().kind = ReliabilityQosPolicyKind::RELIABLE_RELIABILITY_QOS;
        rqos.durability().kind = DurabilityQosPolicyKind::TRANSIENT_LOCAL_DURABILITY_QOS;
        rqos.history().kind = HistoryQosPolicyKind::KEEP_ALL_HISTORY_QOS;

        // CoreData (all variants use the same type)
        TypeSupport cd_type(new CoreData::FlatCoreDataPubSubType());
        cd_type.register_type(ctx.participant);
        ctx.cd_topic = ctx.participant->create_topic("CoreDataTopic", cd_type->get_name(), TOPIC_QOS_DEFAULT);
        ctx.cd2_topic = ctx.participant->create_topic("CoreData2Topic", cd_type->get_name(), TOPIC_QOS_DEFAULT);
        ctx.cd3_topic = ctx.participant->create_topic("CoreData3Topic", cd_type->get_name(), TOPIC_QOS_DEFAULT);
        ctx.cd4_topic = ctx.participant->create_topic("CoreData4Topic", cd_type->get_name(), TOPIC_QOS_DEFAULT);

        // Intelligence
        TypeSupport intel_type(new Intelligence::FlatIntelligencePubSubType());
        intel_type.register_type(ctx.participant);
        ctx.intel_topic = ctx.participant->create_topic("IntelligenceTopic", intel_type->get_name(), TOPIC_QOS_DEFAULT);

        // Messaging
        TypeSupport msg_type(new Messaging::FlatMessagingPacketPubSubType());
        msg_type.register_type(ctx.participant);
        ctx.msg_topic = ctx.participant->create_topic("MessagingTopic", msg_type->get_name(), TOPIC_QOS_DEFAULT);

        // Per-domain listeners with domain tag in logs
        ctx.cd_listener = new CoreDataMonitor(domain_id);
        ctx.intel_listener = new IntelligenceMonitor(domain_id);
        ctx.msg_listener = new MessagingMonitor(domain_id);

        // Readers
        ctx.cd_reader = ctx.cd_topic ? ctx.subscriber->create_datareader(ctx.cd_topic, rqos, ctx.cd_listener) : nullptr;
        ctx.cd2_reader = ctx.cd2_topic ? ctx.subscriber->create_datareader(ctx.cd2_topic, rqos, ctx.cd_listener) : nullptr;
        ctx.cd3_reader = ctx.cd3_topic ? ctx.subscriber->create_datareader(ctx.cd3_topic, rqos, ctx.cd_listener) : nullptr;
        ctx.cd4_reader = ctx.cd4_topic ? ctx.subscriber->create_datareader(ctx.cd4_topic, rqos, ctx.cd_listener) : nullptr;
        ctx.intel_reader = ctx.intel_topic ? ctx.subscriber->create_datareader(ctx.intel_topic, rqos, ctx.intel_listener) : nullptr;
        ctx.msg_reader = ctx.msg_topic ? ctx.subscriber->create_datareader(ctx.msg_topic, rqos, ctx.msg_listener) : nullptr;

        std::cout << "Monitor: DataReaders created for domain " << domain_id << std::endl;

        contexts.push_back(ctx);
    }

    std::cout << "Monitor: Waiting for DDS data on domains 0,1,2,3,4,5..." << std::endl;

    std::signal(SIGINT, [](int){ g_stop.store(true); });
    std::signal(SIGTERM, [](int){ g_stop.store(true); });

    while (!g_stop.load()) {
        std::this_thread::sleep_for(std::chrono::milliseconds(200));
    }

    for (auto& ctx : contexts) {
        if (ctx.subscriber) {
            if (ctx.cd_reader) ctx.subscriber->delete_datareader(ctx.cd_reader);
            if (ctx.cd2_reader) ctx.subscriber->delete_datareader(ctx.cd2_reader);
            if (ctx.cd3_reader) ctx.subscriber->delete_datareader(ctx.cd3_reader);
            if (ctx.cd4_reader) ctx.subscriber->delete_datareader(ctx.cd4_reader);
            if (ctx.intel_reader) ctx.subscriber->delete_datareader(ctx.intel_reader);
            if (ctx.msg_reader) ctx.subscriber->delete_datareader(ctx.msg_reader);
        }

        if (ctx.participant) {
            if (ctx.cd_topic) ctx.participant->delete_topic(ctx.cd_topic);
            if (ctx.cd2_topic) ctx.participant->delete_topic(ctx.cd2_topic);
            if (ctx.cd3_topic) ctx.participant->delete_topic(ctx.cd3_topic);
            if (ctx.cd4_topic) ctx.participant->delete_topic(ctx.cd4_topic);
            if (ctx.intel_topic) ctx.participant->delete_topic(ctx.intel_topic);
            if (ctx.msg_topic) ctx.participant->delete_topic(ctx.msg_topic);

            if (ctx.subscriber) ctx.participant->delete_subscriber(ctx.subscriber);
            factory->delete_participant(ctx.participant);
        }

        delete ctx.cd_listener;
        delete ctx.intel_listener;
        delete ctx.msg_listener;
    }

    return 0;
}
